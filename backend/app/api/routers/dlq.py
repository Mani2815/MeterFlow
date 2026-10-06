from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models.core import DLQEvent
from app.schemas.core import DLQEventSchema
import datetime

router = APIRouter(prefix="/api/v1/dlq", tags=["DLQ"])

@router.get("", response_model=List[DLQEventSchema])
async def list_dlq_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DLQEvent).order_by(DLQEvent.created_at.desc()))
    return result.scalars().all()

@router.post("/{event_id}/replay", response_model=DLQEventSchema)
async def replay_dlq_event(event_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DLQEvent).where(DLQEvent.event_id == event_id))
    event = result.scalars().first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Increment attempt and mark as processing
    event.attempt_count += 1
    event.status = "PROCESSING"
    await db.commit()
    await db.refresh(event)
    
    # In reality, you'd enqueue this payload back into a Pub/Sub topic for processing
    return event
