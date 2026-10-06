import os
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from datetime import datetime, timezone
import json

# Setup structured JSON logging
logging.basicConfig(level=logging.INFO, format='{"time": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "message": "%(message)s"}')
logger = logging.getLogger("control_plane")

app = FastAPI(title="Utility Meter-to-Cash Control Plane")

class IngestionRequest(BaseModel):
    table: str
    batch_size: int = 10000

class BackfillRequest(BaseModel):
    table: str
    start_date: str
    end_date: str

class RunResponse(BaseModel):
    run_id: str
    status: str
    message: str

# Mock state store for runs
_runs_db: Dict[str, Dict[str, Any]] = {}

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    
    # Inject into logger context conceptually
    # In production, use ContextVars for proper async logging context
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", extra={"correlation_id": correlation_id})
        return Response(content=json.dumps({"error": "Internal Server Error"}), status_code=500, media_type="application/json")
        
    response.headers["X-Correlation-ID"] = correlation_id
    return response

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/ingestion/run", response_model=RunResponse)
def run_ingestion(req: IngestionRequest, request: Request):
    run_id = f"ingest_{request.state.correlation_id}"
    logger.info(f"Starting ingestion run {run_id} for {req.table}", extra={"correlation_id": request.state.correlation_id})
    
    if run_id in _runs_db:
        return RunResponse(run_id=run_id, status="SKIPPED", message="Already processed")
        
    _runs_db[run_id] = {"table": req.table, "type": "ingestion", "status": "STARTED"}
    
    return RunResponse(run_id=run_id, status="STARTED", message="Ingestion queued")

@app.post("/backfill", response_model=RunResponse)
def run_backfill(req: BackfillRequest, request: Request):
    run_id = f"bf_{request.state.correlation_id}"
    logger.info(f"Starting backfill {run_id} for {req.table} from {req.start_date} to {req.end_date}", extra={"correlation_id": request.state.correlation_id})
    
    if run_id in _runs_db:
        return RunResponse(run_id=run_id, status="SKIPPED", message="Backfill already processed")
        
    _runs_db[run_id] = {"table": req.table, "type": "backfill", "status": "STARTED"}
    
    return RunResponse(run_id=run_id, status="STARTED", message="Backfill queued")

@app.get("/runs/{run_id}")
def get_run_status(run_id: str):
    run = _runs_db.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run ID not found")
    return {"run_id": run_id, "status": run["status"]}

@app.get("/quality/latest")
def get_latest_quality():
    return {
        "run_id": "latest_001",
        "records_received": 5000,
        "records_rejected": 12,
        "status": "SUCCESS",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
