import argparse
import asyncio
import logging
import os
import glob
import uuid
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from pythonjsonlogger import jsonlogger

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

logger = logging.getLogger("processing.standardize")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://meter:meterpass@db:5432/meter_db")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

LOCAL_GCS_MOCK_DIR = os.getenv("STORAGE_DIR", "/tmp/mock_gcs")

async def record_run(db: AsyncSession, run_id: str, ingestion_run_id: str, dataset: str, source_file: str, status: str, rows_processed: int, bytes_processed: int, output_file: str = None, error_message: str = None):
    from app.models.core import StandardizeRun
    
    result = await db.execute(select(StandardizeRun).where(StandardizeRun.run_id == run_id))
    run = result.scalars().first()
    if not run:
        run = StandardizeRun(
            run_id=run_id,
            ingestion_run_id=ingestion_run_id,
            dataset=dataset,
            source_file=source_file,
            status=status,
            rows_processed=rows_processed,
            bytes_processed=bytes_processed,
            output_file=output_file,
            error_message=error_message
        )
        db.add(run)
    else:
        run.status = status
        run.rows_processed = rows_processed
        run.bytes_processed = bytes_processed
        if output_file:
            run.output_file = output_file
        if error_message:
            run.error_message = error_message
        if status in ["SUCCESS", "FAILED"]:
            run.completed_at = datetime.now()
    
    await db.commit()

async def standardize_smartmeter(ingestion_run_id: str):
    logger.info("Starting standardization", extra={"ingestion_run_id": ingestion_run_id})
    
    db = AsyncSessionLocal()
    run_id = str(uuid.uuid4())
    
    # 1. Find all raw chunks for this ingestion_run_id
    raw_dir = os.path.join(LOCAL_GCS_MOCK_DIR, f"utility/raw/smartmeter/Small LCL Data/LCL-June2015v2_0.csv/run={ingestion_run_id}")
    # Wait, the filename path could be dynamic. We need to glob for run_id
    pattern = os.path.join(LOCAL_GCS_MOCK_DIR, f"utility/raw/smartmeter/**/run={ingestion_run_id}/*.json")
    files = glob.glob(pattern, recursive=True)
    
    if not files:
        logger.warning("No raw files found for ingestion run", extra={"ingestion_run_id": ingestion_run_id})
        await db.close()
        return

    source_path = os.path.dirname(files[0])
    
    await record_run(db, run_id, ingestion_run_id, "smartmeter", source_path, "RUNNING", 0, 0)
    
    total_rows = 0
    total_bytes = 0
    
    try:
        dataframes = []
        for file in files:
            file_bytes = os.path.getsize(file)
            total_bytes += file_bytes
            
            # Read JSON records line by line (ndjson)
            df = pd.read_json(file, lines=True)
            if not df.empty:
                dataframes.append(df)
        
        if not dataframes:
            raise ValueError("All chunks were empty")
            
        combined_df = pd.concat(dataframes, ignore_index=True)
        total_rows = len(combined_df)
        
        # 2. Schema Validation & Type Casting
        # Expected: meter_id(str), household_id(str), event_timestamp(datetime), consumption_kwh(float), source_system(str)
        combined_df['meter_id'] = combined_df['meter_id'].astype(str)
        combined_df['household_id'] = combined_df['household_id'].astype(str)
        combined_df['event_timestamp'] = pd.to_datetime(combined_df['event_timestamp'], utc=True)
        combined_df['consumption_kwh'] = pd.to_numeric(combined_df['consumption_kwh'], errors='coerce').fillna(0.0)
        
        if 'stdorToU' in combined_df.columns:
            combined_df = combined_df.rename(columns={'stdorToU': 'stdor_to_u'})
            combined_df['stdor_to_u'] = combined_df['stdor_to_u'].astype(str)
        else:
            combined_df['stdor_to_u'] = None
            
        combined_df['source_system'] = combined_df['source_system'].astype(str)
        
        # 3. Add audit columns
        combined_df['processed_at'] = pd.Timestamp.utcnow()
        combined_df['ingestion_run_id'] = ingestion_run_id
        combined_df['standardize_run_id'] = run_id
        
        # 4. Write to Parquet (Standardized Zone)
        output_dir = os.path.join(LOCAL_GCS_MOCK_DIR, "utility/standardized/smartmeter")
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"run_{ingestion_run_id}.parquet")
        
        table = pa.Table.from_pandas(combined_df)
        pq.write_table(table, output_file, compression='snappy')
        
        logger.info("Standardization successful", extra={
            "ingestion_run_id": ingestion_run_id,
            "standardize_run_id": run_id,
            "rows": total_rows,
            "output_file": output_file
        })
        
        await record_run(db, run_id, ingestion_run_id, "smartmeter", source_path, "SUCCESS", total_rows, total_bytes, output_file=output_file)
        
    except Exception as e:
        logger.error("Standardization failed", extra={"ingestion_run_id": ingestion_run_id, "error": str(e)})
        await record_run(db, run_id, ingestion_run_id, "smartmeter", source_path, "FAILED", 0, 0, error_message=str(e))
        
    finally:
        await db.close()

async def list_runs():
    db = AsyncSessionLocal()
    from app.models.core import StandardizeRun
    result = await db.execute(select(StandardizeRun).order_by(StandardizeRun.started_at.desc()).limit(10))
    runs = result.scalars().all()
    print("Recent Standardize Runs:")
    for r in runs:
        print(f"{r.run_id} | Ingestion: {r.ingestion_run_id} | Status: {r.status} | Rows: {r.rows_processed}")
    await db.close()

def main():
    parser = argparse.ArgumentParser(description="Standardize Processing")
    subparsers = parser.add_subparsers(dest="command")
    
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("dataset", type=str)
    run_parser.add_argument("--ingestion-run-id", type=str, required=True)
    
    status_parser = subparsers.add_parser("status")
    
    args = parser.parse_args()
    
    if args.command == "run":
        if args.dataset == "smartmeter":
            asyncio.run(standardize_smartmeter(args.ingestion_run_id))
    elif args.command == "status":
        asyncio.run(list_runs())

if __name__ == "__main__":
    main()
