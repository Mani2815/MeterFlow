from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models.master_data import (
    SyntheticCustomer, 
    SyntheticAccount, 
    SyntheticServicePoint, 
    SyntheticContract, 
    SyntheticMeter
)

router = APIRouter(prefix="/master-data", tags=["Master Data (Synthetic)"])

@router.get("/customers")
async def get_customers(skip: int = Query(0), limit: int = Query(50), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SyntheticCustomer).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SyntheticCustomer).where(SyntheticCustomer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.get("/accounts")
async def get_accounts(skip: int = Query(0), limit: int = Query(50), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SyntheticAccount).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/contracts")
async def get_contracts(skip: int = Query(0), limit: int = Query(50), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SyntheticContract).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/service-points")
async def get_service_points(skip: int = Query(0), limit: int = Query(50), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SyntheticServicePoint).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/meters")
async def get_meters(skip: int = Query(0), limit: int = Query(50), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SyntheticMeter)
        .options(selectinload(SyntheticMeter.service_point))
        .offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/meters/{meter_id}")
async def get_meter(meter_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SyntheticMeter)
        .options(selectinload(SyntheticMeter.service_point))
        .where(SyntheticMeter.id == meter_id)
    )
    meter = result.scalars().first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    return meter
