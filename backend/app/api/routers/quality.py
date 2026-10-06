from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.core import DataQualityRun, DLQEvent
from app.schemas.core import QualitySummarySchema

router = APIRouter(prefix="/api/v1/data-quality", tags=["Data Quality"])

@router.get("/summary", response_model=QualitySummarySchema)
async def get_quality_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(
        func.avg(DataQualityRun.overall_score),
        func.avg(DataQualityRun.completeness),
        func.avg(DataQualityRun.validity),
        func.avg(DataQualityRun.uniqueness)
    ))
    row = result.first()
    
    return QualitySummarySchema(
        overall_score=round(row[0] or 100.0, 1),
        completeness=round(row[1] or 100.0, 1),
        validity=round(row[2] or 100.0, 1),
        uniqueness=round(row[3] or 100.0, 1),
        consistency=100.0, # Not currently measured
        timeliness=100.0 # Not currently measured
    )

@router.get("/issues")
async def get_active_issues(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DLQEvent).where(DLQEvent.status == "PENDING").order_by(DLQEvent.created_at.desc()).limit(100))
    events = result.scalars().all()
    return events
