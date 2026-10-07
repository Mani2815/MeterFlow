import argparse
import asyncio
import logging
import os
import uuid
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from pythonjsonlogger import jsonlogger

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

logger = logging.getLogger("processing.quality")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://meter_user:meter_pass@localhost:5432/meter_to_cash")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

LOCAL_GCS_MOCK_DIR = "/tmp/mock_gcs"

async def record_dlq_event(db: AsyncSession, row: pd.Series, error_type: str, error_message: str):
    from app.models.core import DLQEvent
    event = DLQEvent(
        event_id=str(uuid.uuid4()),
        source="uk_power_networks",
        dataset="smartmeter",
        error_type=error_type,
        error_message=error_message,
        payload_reference=str(row.to_dict())[:500] # store JSON snippet of bad row
    )
    db.add(event)

async def run_data_quality(standardize_run_id: str):
    logger.info("Starting data quality checks", extra={"standardize_run_id": standardize_run_id})
    db = AsyncSessionLocal()
    
    try:
        from app.models.core import StandardizeRun, DataQualityRun
        
        # 1. Fetch standardize run to get the output_file
        result = await db.execute(select(StandardizeRun).where(StandardizeRun.run_id == standardize_run_id))
        std_run = result.scalars().first()
        if not std_run or not std_run.output_file:
            logger.error("Standardize run not found or has no output file", extra={"standardize_run_id": standardize_run_id})
            return
            
        parquet_file = std_run.output_file
        if not os.path.exists(parquet_file):
            logger.error("Parquet file does not exist", extra={"file": parquet_file})
            return
            
        # 2. Load Parquet
        df = pd.read_parquet(parquet_file)
        total_rows = len(df)
        if total_rows == 0:
            logger.warning("Empty dataframe")
            return
            
        # 3. Apply Quality Rules
        # Completeness: must have meter_id and event_timestamp
        df['is_complete'] = df['meter_id'].notna() & df['event_timestamp'].notna()
        
        # Validity: consumption >= 0 and consumption < 100 kWh/half-hour (physically impossible for normal household)
        df['is_valid'] = (df['consumption_kwh'] >= 0) & (df['consumption_kwh'] <= 100)
        
        # Uniqueness: group by meter_id + event_timestamp
        df['is_unique'] = ~df.duplicated(subset=['meter_id', 'event_timestamp'], keep='first')
        
        # Overall quality
        df['is_good'] = df['is_complete'] & df['is_valid'] & df['is_unique']
        
        good_df = df[df['is_good']].copy()
        bad_df = df[~df['is_good']].copy()
        
        completeness_score = (df['is_complete'].sum() / total_rows) * 100
        validity_score = (df['is_valid'].sum() / total_rows) * 100
        uniqueness_score = (df['is_unique'].sum() / total_rows) * 100
        overall_score = (len(good_df) / total_rows) * 100
        
        logger.info("Quality evaluation complete", extra={
            "total_rows": total_rows,
            "good_rows": len(good_df),
            "bad_rows": len(bad_df),
            "completeness": completeness_score,
            "validity": validity_score
        })
        
        # 4. Write DLQ Events
        # For performance, only insert up to 100 DLQ events if there are many
        for idx, row in bad_df.head(100).iterrows():
            error_msg = []
            if not row['is_complete']: error_msg.append("Missing required fields")
            if not row['is_valid']: error_msg.append("Anomalous consumption value")
            if not row['is_unique']: error_msg.append("Duplicate reading")
            
            await record_dlq_event(db, row, "VALIDATION_FAILED", " | ".join(error_msg))
            
        # 5. Save Valid rows to Gold Zone
        if not good_df.empty:
            output_dir = os.path.join(LOCAL_GCS_MOCK_DIR, "utility/gold/smartmeter")
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"gold_{standardize_run_id}.parquet")
            
            # Drop the temp quality columns
            good_df = good_df.drop(columns=['is_complete', 'is_valid', 'is_unique', 'is_good'])
            table = pa.Table.from_pandas(good_df)
            pq.write_table(table, output_file, compression='snappy')
            
        # 6. Record Data Quality Run
        dq_run = DataQualityRun(
            id=str(uuid.uuid4()),
            run_id=standardize_run_id,
            dataset="smartmeter",
            overall_score=overall_score,
            completeness=completeness_score,
            validity=validity_score,
            uniqueness=uniqueness_score
        )
        db.add(dq_run)
        await db.commit()
        
    except Exception as e:
        logger.error("Data Quality check failed", extra={"error": str(e)})
    finally:
        await db.close()

def main():
    parser = argparse.ArgumentParser(description="Data Quality Engine")
    subparsers = parser.add_subparsers(dest="command")
    
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--standardize-run-id", type=str, required=True)
    
    args = parser.parse_args()
    if args.command == "run":
        asyncio.run(run_data_quality(args.standardize_run_id))

if __name__ == "__main__":
    main()
