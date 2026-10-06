from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
import subprocess

from app.database import get_db
from app.models.core import StandardizeRun

router = APIRouter()

@router.get("/processing/runs")
async def list_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StandardizeRun).order_by(StandardizeRun.started_at.desc()).limit(50))
    runs = result.scalars().all()
    return runs

@router.get("/processing/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count(StandardizeRun.run_id)))
    total_runs = result.scalar() or 0
    
    if total_runs == 0:
        return {
            "status": "Not configured",
            "last_run": None,
            "processed_resources": 0,
            "total_rows": 0
        }
        
    result = await db.execute(select(StandardizeRun).order_by(StandardizeRun.started_at.desc()).limit(1))
    last_run = result.scalars().first()
    
    result = await db.execute(select(func.sum(StandardizeRun.rows_processed)))
    total_rows = result.scalar() or 0
    
    result = await db.execute(select(func.count(StandardizeRun.run_id)).where(StandardizeRun.status == 'SUCCESS'))
    successful_runs = result.scalar() or 0
    
    return {
        "status": "Operational",
        "last_run": last_run.started_at if last_run else None,
        "processed_resources": successful_runs,
        "total_rows": total_rows
    }

def trigger_standardize_subprocess(ingestion_run_id: str):
    subprocess.Popen([
        "python", "-m", "app.processing.standardize", "run", "smartmeter", "--ingestion-run-id", ingestion_run_id
    ])

@router.post("/processing/standardize")
async def trigger_standardize(payload: dict, background_tasks: BackgroundTasks):
    ingestion_run_id = payload.get("ingestion_run_id")
    if not ingestion_run_id:
        raise HTTPException(status_code=400, detail="ingestion_run_id is required")
        
    background_tasks.add_task(trigger_standardize_subprocess, ingestion_run_id)
    return {"message": "Standardization triggered", "ingestion_run_id": ingestion_run_id}
