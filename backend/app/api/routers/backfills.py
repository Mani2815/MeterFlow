from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models.core import BackfillJob
from app.schemas.core import BackfillRequest, BackfillSchema
import uuid
import datetime

router = APIRouter(prefix="/api/v1/backfills", tags=["Backfills"])

@router.get("", response_model=List[BackfillSchema])
async def list_backfills(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BackfillJob).order_by(BackfillJob.created_at.desc()))
    return result.scalars().all()

@router.post("", response_model=BackfillSchema)
async def create_backfill(req: BackfillRequest, db: AsyncSession = Depends(get_db)):
    bf_id = f"BF-{datetime.datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:4]}"
    
    new_bf = BackfillJob(
        backfill_id=bf_id,
        dataset=req.dataset,
        start_date=req.start_date,
        end_date=req.end_date,
        status="PENDING"
    )
    db.add(new_bf)
    await db.commit()
    await db.refresh(new_bf)
    
    return new_bf

@router.get("/{backfill_id}", response_model=BackfillSchema)
async def get_backfill(backfill_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BackfillJob).where(BackfillJob.backfill_id == backfill_id))
    bf = result.scalars().first()
    if not bf:
        raise HTTPException(status_code=404, detail="Backfill not found")
    return bf
