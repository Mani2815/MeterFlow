from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
import subprocess

from app.database import get_db
from app.models.core import IngestionRun

router = APIRouter()

@router.get("/sources")
async def get_sources():
    return [
        {
            "id": "smartmeter",
            "provider": "uk_power_networks",
            "name": "SmartMeter Energy Consumption Data in London Households",
            "status": "Connected"
        }
    ]

@router.get("/sources/{source_id}")
async def get_source(source_id: str):
    if source_id != "smartmeter":
        raise HTTPException(status_code=404, detail="Source not found")
    return {
        "id": "smartmeter",
        "provider": "uk_power_networks",
        "url": "https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d",
        "resources": 168
    }

@router.get("/ingestion/runs")
async def list_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(50))
    runs = result.scalars().all()
    return runs

@router.get("/ingestion/runs/{run_id}")
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IngestionRun).where(IngestionRun.run_id == run_id))
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/ingestion/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    # Count total runs
    result = await db.execute(select(func.count(IngestionRun.run_id)))
    total_runs = result.scalar() or 0
    
    if total_runs == 0:
        return {
            "status": "Not configured",
            "last_run": None,
            "processed_resources": 0,
            "total_rows": 0
        }
        
    # Get last run
    result = await db.execute(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(1))
    last_run = result.scalars().first()
    
    # Get total rows
    result = await db.execute(select(func.sum(IngestionRun.rows_received)))
    total_rows = result.scalar() or 0
    
    # Get successful runs
    result = await db.execute(select(func.count(IngestionRun.run_id)).where(IngestionRun.status == 'SUCCESS'))
    successful_runs = result.scalar() or 0
    
    return {
        "status": "Connected",
        "last_run": last_run.started_at if last_run else None,
        "processed_resources": successful_runs,
        "total_rows": total_rows
    }

def trigger_ingestion_subprocess(target_file: str, mode: str):
    # Runs the ingestion in a subprocess so it doesn't block the API
    subprocess.Popen([
        "python", "-m", "app.ingestion.smartmeter", "source", "smartmeter", "--file", target_file, "--mode", mode
    ])

@router.post("/ingestion/smartmeter")
async def trigger_ingestion(payload: dict, background_tasks: BackgroundTasks):
    resource = payload.get("resource", "1")
    mode = payload.get("mode", "test")
    
    background_tasks.add_task(trigger_ingestion_subprocess, resource, mode)
    
    return {"message": "Ingestion triggered", "resource": resource, "mode": mode}
