from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models.core import Pipeline, PipelineRun
from app.schemas.core import PipelineSchema, PipelineRunSchema, PipelineRunRequest
import uuid
import datetime

router = APIRouter(prefix="/api/v1/pipelines", tags=["Pipelines"])

@router.get("", response_model=List[PipelineSchema])
async def list_pipelines(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pipeline))
    return result.scalars().all()

@router.get("/{pipeline_id}", response_model=PipelineSchema)
async def get_pipeline(pipeline_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalars().first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline

@router.get("/{pipeline_id}/runs", response_model=List[PipelineRunSchema])
async def get_pipeline_runs(pipeline_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PipelineRun).where(PipelineRun.pipeline_id == pipeline_id).order_by(PipelineRun.started_at.desc()))
    return result.scalars().all()

@router.post("/{pipeline_id}/run", response_model=PipelineRunSchema)
async def trigger_pipeline_run(pipeline_id: str, req: PipelineRunRequest, db: AsyncSession = Depends(get_db)):
    # Verify pipeline exists
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalars().first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Create run record
    new_run = PipelineRun(
        run_id=f"RUN-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}",
        pipeline_id=pipeline_id,
        status="STARTED",
        trigger_type=req.trigger_type
    )
    db.add(new_run)
    await db.commit()
    await db.refresh(new_run)
    
    # In a real system, you would enqueue a Pub/Sub message or trigger Cloud Run/Dataflow here
    # For now, we just record the operational intent in Postgres
    return new_run
