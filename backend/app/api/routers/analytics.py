from fastapi import APIRouter, HTTPException, Depends
from google.cloud import bigquery
from pydantic import BaseModel
from typing import List, Optional
import os
import glob
import pandas as pd

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.core import DataQualityRun, IngestionRun, StandardizeRun, DLQEvent

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

PROJECT_ID = os.getenv("GCP_PROJECT", "meter-to-cash-project")
DATASET_ID = "utility_analytics"
TABLE_ID = "fact_meter_reading"
TABLE_PATH = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
GOLD_DIR = "/tmp/mock_gcs/utility/gold/smartmeter/"

def get_bq_client():
    try:
        return bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"BigQuery Service Unavailable: {str(e)}")

def get_latest_gold_df() -> pd.DataFrame:
    """Read the most recently created Gold Parquet file."""
    files = glob.glob(os.path.join(GOLD_DIR, "*.parquet"))
    if not files:
        return pd.DataFrame()
    latest = max(files, key=os.path.getctime)
    return pd.read_parquet(latest)

@router.get("/gold-stats")
def get_gold_stats():
    """
    Returns real dataset statistics directly from the Gold Parquet zone.
    Available without BigQuery credentials.
    """
    df = get_latest_gold_df()
    if df.empty:
        return {"available": False, "message": "No Gold data found. Run the ingestion pipeline first."}

    tariff_counts = df['stdor_to_u'].value_counts().to_dict() if 'stdor_to_u' in df.columns else {}
    try:
        min_ts = str(df['event_timestamp'].min())
        max_ts = str(df['event_timestamp'].max())
    except Exception:
        min_ts = None
        max_ts = None

    return {
        "available": True,
        "total_rows": len(df),
        "distinct_households": int(df['household_id'].nunique()) if 'household_id' in df.columns else 0,
        "total_consumption_kwh": float(round(df['consumption_kwh'].sum(), 2)) if 'consumption_kwh' in df.columns else 0,
        "tariff_distribution": tariff_counts,
        "date_range": {"from": min_ts, "to": max_ts},
        "columns": list(df.columns),
        "source_system": "uk_power_networks",
        "storage_zone": "Gold (Parquet)",
        "storage_path": GOLD_DIR,
    }

@router.get("/pipeline-summary")
async def get_pipeline_summary(db: AsyncSession = Depends(get_db)):
    """
    Returns a full UKPN -> Raw -> Standardized -> Gold pipeline summary
    using real metadata from PostgreSQL.
    """
    # Raw (IngestionRun)
    ingest_result = await db.execute(
        select(func.count(IngestionRun.run_id), func.sum(IngestionRun.rows_received))
    )
    ingest_row = ingest_result.first()
    total_ingest_runs = ingest_row[0] or 0
    total_raw_rows = int(ingest_row[1] or 0)

    last_ingest = await db.execute(
        select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(1)
    )
    last_ingest_run = last_ingest.scalars().first()

    # Standardized (StandardizeRun)
    std_result = await db.execute(
        select(func.count(StandardizeRun.run_id), func.sum(StandardizeRun.rows_processed))
    )
    std_row = std_result.first()
    total_std_runs = std_row[0] or 0
    total_std_rows = int(std_row[1] or 0)

    # Quality / Gold — derive from Gold Parquet since DataQualityRun doesn't store row counts
    import glob as _glob
    import os as _os
    gold_files = _glob.glob("/tmp/mock_gcs/utility/gold/smartmeter/*.parquet")
    gold_rows = 0
    if gold_files:
        import pandas as _pd
        latest_gold = max(gold_files, key=_os.path.getctime)
        _gdf = _pd.read_parquet(latest_gold)
        gold_rows = len(_gdf)

    dq_result = await db.execute(
        select(
            func.avg(DataQualityRun.overall_score),
            func.count(DataQualityRun.id)
        )
    )
    dq_row = dq_result.first()
    avg_quality = round(float(dq_row[0] or 100.0), 1)
    total_rejected = total_std_rows - gold_rows if total_std_rows > gold_rows else 0


    # DLQ
    dlq_result = await db.execute(select(func.count(DLQEvent.event_id)))
    dlq_count = int(dlq_result.scalar() or 0)

    return {
        "stages": [
            {
                "name": "UKPN Source",
                "status": "ACTIVE",
                "description": "SmartMeter Energy Consumption Data in London Households",
                "url": "https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d",
                "format": "168 CSV files in ZIP archive",
                "rows": None,
            },
            {
                "name": "Raw",
                "status": "PASS" if total_ingest_runs > 0 else "PENDING",
                "runs": total_ingest_runs,
                "rows": total_raw_rows,
                "last_run": str(last_ingest_run.started_at) if last_ingest_run else None,
                "format": "NDJSON",
                "fields": ["meter_id", "household_id", "event_timestamp", "consumption_kwh", "stdorToU", "source_system"],
            },
            {
                "name": "Standardized",
                "status": "PASS" if total_std_runs > 0 else "PENDING",
                "runs": total_std_runs,
                "rows": total_std_rows,
                "format": "Parquet (Snappy)",
                "fields": ["meter_id", "household_id", "event_timestamp", "consumption_kwh", "stdor_to_u", "processed_at", "ingestion_run_id"],
            },
            {
                "name": "Gold",
                "status": "PASS" if gold_rows > 0 else "PENDING",
                "rows": gold_rows,
                "rejected": total_rejected,
                "dlq": dlq_count,
                "quality_score": avg_quality,
                "format": "Parquet (Snappy)",
                "fields": ["meter_id", "household_id", "event_timestamp", "consumption_kwh", "stdor_to_u", "standardize_run_id"],
            },
            {
                "name": "Local Parquet",
                "status": "PASS" if gold_rows > 0 else "PENDING",
                "description": "Served directly from local Parquet without BigQuery.",
                "rows": gold_rows,
            }
        ]
    }

@router.get("/summary")
def get_analytics_summary():
    """Dataset overview (unique households, reading count, date range)"""
    df = get_latest_gold_df()
    if df.empty:
        return {"unique_households": 0, "reading_count": 0, "total_consumption": 0}
        
    return {
        "unique_households": int(df['household_id'].nunique()) if 'household_id' in df.columns else 0,
        "reading_count": len(df),
        "min_date": str(df['event_timestamp'].min()) if 'event_timestamp' in df.columns else None,
        "max_date": str(df['event_timestamp'].max()) if 'event_timestamp' in df.columns else None,
        "total_consumption": float(round(df['consumption_kwh'].sum(), 2)) if 'consumption_kwh' in df.columns else 0
    }

@router.get("/consumption/daily")
def get_daily_consumption():
    """Daily consumption for time-series charts"""
    df = get_latest_gold_df()
    if df.empty or 'event_timestamp' not in df.columns or 'consumption_kwh' not in df.columns:
        return []
        
    df['day'] = pd.to_datetime(df['event_timestamp']).dt.date
    daily = df.groupby('day')['consumption_kwh'].sum().reset_index()
    daily = daily.sort_values('day', ascending=False).head(30)
    
    return [{"day": str(row['day']), "consumption": float(row['consumption_kwh'])} for _, row in daily.iterrows()]

@router.get("/households")
def get_household_analytics():
    df = get_latest_gold_df()
    if df.empty or 'household_id' not in df.columns or 'consumption_kwh' not in df.columns:
        return []
        
    hh = df.groupby('household_id').agg(
        total_consumption=('consumption_kwh', 'sum'),
        reading_count=('consumption_kwh', 'count')
    ).reset_index()
    hh = hh.sort_values('total_consumption', ascending=False).head(10)
    
    return [{"source_household_id": row['household_id'], "total_consumption": float(row['total_consumption']), "reading_count": int(row['reading_count'])} for _, row in hh.iterrows()]

@router.get("/tariffs")
def get_tariff_analytics():
    """Tariff breakdown and statistics."""
    df = get_latest_gold_df()
    if df.empty or 'stdor_to_u' not in df.columns or 'household_id' not in df.columns or 'consumption_kwh' not in df.columns:
        return []
        
    tariffs = df.groupby('stdor_to_u').agg(
        household_count=('household_id', 'nunique'),
        total_readings=('consumption_kwh', 'count'),
        total_consumption_kwh=('consumption_kwh', 'sum')
    ).reset_index()
    tariffs = tariffs.sort_values('household_count', ascending=False)
    
    return [{"tariff_code": row['stdor_to_u'], "household_count": int(row['household_count']), "total_readings": int(row['total_readings']), "total_consumption_kwh": float(row['total_consumption_kwh'])} for _, row in tariffs.iterrows()]

@router.get("/data-quality")
async def get_data_quality_stats(db: AsyncSession = Depends(get_db)):
    """Use actual quality metadata from PostgreSQL pipeline control plane."""
    result = await db.execute(select(
        func.avg(DataQualityRun.overall_score),
        func.count(DataQualityRun.id)
    ))
    row = result.first()
    return {
        "average_quality_score": round(row[0] or 100.0, 1),
        "total_quality_runs": row[1] or 0
    }
