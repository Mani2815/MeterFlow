import os
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger
import logging

from app.api.routers import pipelines, backfills, dlq, quality, ingestion, processing, analytics, master_data

# Setup structured JSON logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(correlation_id)s %(message)s"
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

app = FastAPI(title="Utility Meter-to-Cash Data Platform API")

# Setup CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the real frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# Include routers
app.include_router(pipelines.router)
app.include_router(backfills.router)
app.include_router(dlq.router)
app.include_router(quality.router)
app.include_router(ingestion.router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(processing.router, prefix="/api/v1", tags=["Processing"])
app.include_router(analytics.router)
app.include_router(master_data.router, prefix="/api/v1")

@app.get("/api/v1/health", tags=["System"])
def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.core import IngestionRun, DLQEvent, DataQualityRun

@app.get("/api/v1/dashboard/summary", tags=["Dashboard"])
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """
    Returns high-level platform metrics for the Overview page.
    """
    # Real records processed
    records_processed_today = await db.execute(select(func.sum(IngestionRun.rows_received)))
    total_records = records_processed_today.scalar() or 0
    
    # Real failed runs
    failed_runs = await db.execute(select(func.count(IngestionRun.run_id)).where(IngestionRun.status == 'FAILED'))
    total_failed = failed_runs.scalar() or 0
    
    # Real DLQ count
    dlq_count = await db.execute(select(func.count(DLQEvent.event_id)))
    total_dlq = dlq_count.scalar() or 0
    
    # Real active sources
    active_sources = await db.execute(select(func.count(func.distinct(IngestionRun.source))))
    total_active_sources = active_sources.scalar() or 0

    # Real quality score
    quality_score_result = await db.execute(select(func.avg(DataQualityRun.overall_score)))
    quality_score = quality_score_result.scalar()
    quality_score = round(quality_score, 1) if quality_score is not None else 0.0

    return {
        "records_processed_today": total_records,
        "quality_score": quality_score,
        "failed_runs": total_failed,
        "dlq_count": total_dlq,
        "active_sources": total_active_sources
    }
