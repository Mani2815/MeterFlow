import argparse
import asyncio
import csv
import io
import json
import logging
import os
import tempfile
import time
import uuid
import zipfile
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from google.cloud import storage

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Setup structured logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("ingestion.smartmeter")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Dataset URLs
PARTITIONED_ZIP_URL = "https://data.london.gov.uk/download/vqm0d/04feba67-f1a3-4563-98d0-f3071e3d56d1/Partitioned%20LCL%20Data.zip"
TARIFFS_URL = "https://data.london.gov.uk/download/vqm0d/14855047-44c2-4856-8a48-e5649200e6ce/Tariffs.xlsx"

# Database Configuration (fallback to defaults if not in env)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://meter:meterpass@db:5432/meter_db")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# For testing locally without GCP credentials
LOCAL_GCS_MOCK_DIR = os.getenv("STORAGE_DIR", "/tmp/mock_gcs")

def get_db():
    return AsyncSessionLocal()

def download_file(url: str, dest_path: str):
    logger.info("Starting download", extra={"url": url, "dest": dest_path})
    # Basic exponential backoff for resilience
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with httpx.stream("GET", url, timeout=60.0) as response:
                response.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
            logger.info("Download completed successfully")
            return
        except httpx.HTTPStatusError as e:
            logger.warning("HTTP error during download", extra={"status_code": e.response.status_code})
            if e.response.status_code == 429:
                logger.warning("HTTP 429 Too Many Requests, retrying...")
                time.sleep(2 ** attempt)
                continue
            raise
        except Exception as e:
            logger.error("Download failed", extra={"error": str(e)})
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)

def validate_row(row: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Validate and normalize a single row from the smartmeter dataset."""
    try:
        # Expected columns: LCLid, stdorToU, DateTime, KWH/hh (per half hour)
        lcl_id = row.get("LCLid")
        if not lcl_id:
            return None
        
        # Parse timestamp
        dt_str = row.get("DateTime", "")
        # Format usually: YYYY-MM-DD HH:MM:SS or similar
        try:
            event_timestamp = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.0000000")
        except ValueError:
            # Fallback if different format
            event_timestamp = datetime.now() # Mock for unparseable in this demo
            
        consumption_str = row.get("KWH/hh (per half hour)", "0")
        if consumption_str.strip() == "Null":
            consumption = 0.0
        else:
            consumption = float(consumption_str)
            
        # Simulate meter ID from household ID
        simulated_meter_id = f"METER-{lcl_id.replace('MAC', '')}"
        
        # Preserve tariff type exactly as in source
        stdor_to_u = row.get("stdorToU")
        
        return {
            "meter_id": simulated_meter_id,
            "household_id": lcl_id,
            "event_timestamp": event_timestamp.isoformat(),
            "consumption_kwh": consumption,
            "stdorToU": stdor_to_u,
            "source_system": "uk_power_networks"
        }
    except Exception:
        return None

def process_csv_file(file_obj, filename: str, run_id: str, mode: str):
    logger.info("Processing CSV file", extra={"source_file": filename, "run_id": run_id})
    text_io = io.TextIOWrapper(file_obj, encoding='utf-8')
    reader = csv.DictReader(text_io)
    
    rows_read = 0
    rows_valid = 0
    rows_invalid = 0
    
    valid_records = []
    
    for row in reader:
        rows_read += 1
        normalized = validate_row(row)
        if normalized:
            valid_records.append(normalized)
            rows_valid += 1
        else:
            rows_invalid += 1
            
        # Write chunks to avoid loading millions of rows into memory
        if len(valid_records) >= 50000:
            write_chunk_to_storage(valid_records, filename, run_id, mode, chunk_index=rows_read)
            valid_records.append({"stats": f"Mock flush at {rows_read}"}) # Just to prevent completely clearing if needed
            valid_records.clear()
            
        # In test mode, we bail early to save time
        if mode == "test" and rows_read >= 1000:
            break
            
    if valid_records:
        write_chunk_to_storage(valid_records, filename, run_id, mode, chunk_index=rows_read)

    logger.info("File processing completed", extra={
        "source_file": filename,
        "rows_read": rows_read,
        "rows_valid": rows_valid,
        "rows_invalid": rows_invalid
    })
    return rows_read, rows_valid

def write_chunk_to_storage(records: List[Dict], filename: str, run_id: str, mode: str, chunk_index: int):
    # This simulates pushing to GCS Raw zone
    bucket_name = os.getenv("GCS_RAW_BUCKET", "meter-raw-zone")
    blob_path = f"utility/raw/smartmeter/{filename}/run={run_id}/chunk_{chunk_index}.json"
    
    data = "\n".join(json.dumps(r) for r in records if "meter_id" in r)
    
    if mode == "cloud":
        try:
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            blob.upload_from_string(data)
        except Exception as e:
            logger.error("GCS Upload failed", extra={"error": str(e)})
    else:
        # Test mode, write to local mock dir
        local_path = os.path.join(LOCAL_GCS_MOCK_DIR, blob_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "w") as f:
            f.write(data)

async def record_run(db: AsyncSession, run_id: str, source_file: str, status: str, rows_received: int, bytes_received: int):
    from app.models.core import IngestionRun
    
    result = await db.execute(select(IngestionRun).where(IngestionRun.run_id == run_id))
    run = result.scalars().first()
    if not run:
        run = IngestionRun(
            run_id=run_id,
            source="uk_power_networks",
            dataset="smartmeter",
            source_file=source_file,
            status=status,
            rows_received=rows_received,
            bytes_received=bytes_received
        )
        db.add(run)
    else:
        run.status = status
        run.rows_received = rows_received
        run.bytes_received = bytes_received
        if status in ["SUCCESS", "FAILED"]:
            run.completed_at = datetime.now()
    
    await db.commit()

async def run_ingestion(target_files: List[str], mode: str):
    logger.info("Starting ingestion run", extra={"mode": mode, "target_files": target_files})
    
    # 1. Prepare Zip File
    zip_path = "/tmp/Partitioned_LCL_Data.zip"
    if not os.path.exists(zip_path):
        logger.info("Zip file not found locally, downloading...")
        download_file(PARTITIONED_ZIP_URL, zip_path)
    else:
        logger.info("Using cached zip file in /tmp")
        
    db = get_db()
    
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            available_files = [f for f in z.namelist() if f.endswith(".csv")]
            
            files_to_process = available_files
            if "all" not in target_files:
                # Filter to requested files (e.g., '1' -> 'MAC000002.csv' or similar). 
                # For simplicity, if they specify '1', we process the 1st file in the zip.
                indices = []
                for t in target_files:
                    try:
                        indices.append(int(t) - 1)
                    except ValueError:
                        pass
                if indices:
                    files_to_process = [available_files[i] for i in indices if 0 <= i < len(available_files)]
            
            for filename in files_to_process:
                run_id = str(uuid.uuid4())
                await record_run(db, run_id, filename, "RUNNING", 0, 0)
                
                try:
                    with z.open(filename) as f:
                        file_info = z.getinfo(filename)
                        bytes_received = file_info.file_size
                        
                        rows_read, rows_valid = process_csv_file(f, filename, run_id, mode)
                        
                        await record_run(db, run_id, filename, "SUCCESS", rows_valid, bytes_received)
                except Exception as e:
                    logger.error("Error processing file", extra={"source_file": filename, "error": str(e)})
                    await record_run(db, run_id, filename, "FAILED", 0, 0)
                    
    except Exception as e:
        logger.error("Fatal ingestion error", extra={"error": str(e)})
        
    finally:
        await db.close()

def main():
    parser = argparse.ArgumentParser(description="Ingest SmartMeter Data")
    subparsers = parser.add_subparsers(dest="command")
    
    # ingest source smartmeter --file 001
    source_parser = subparsers.add_parser("source")
    source_parser.add_argument("dataset", type=str)
    source_parser.add_argument("--file", type=str, action="append")
    source_parser.add_argument("--files", type=str)
    source_parser.add_argument("--all", action="store_true")
    source_parser.add_argument("--mode", type=str, default="test", choices=["test", "cloud"])
    
    status_parser = subparsers.add_parser("status")
    
    args = parser.parse_args()
    
    if args.command == "source" and args.dataset == "smartmeter":
        targets = []
        if args.all:
            targets = ["all"]
        elif args.files:
            targets = args.files.split(",")
        elif args.file:
            targets = args.file
        else:
            targets = ["1"] # Default to first file for dev
            
        asyncio.run(run_ingestion(targets, args.mode))
        
    elif args.command == "status":
        async def fetch_status():
            db = get_db()
            from app.models.core import IngestionRun
            result = await db.execute(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(10))
            runs = result.scalars().all()
            print("Recent Ingestion Runs:")
            for r in runs:
                print(f"{r.run_id} | {r.source_file} | {r.status} | Rows: {r.rows_received} | Bytes: {r.bytes_received}")
            await db.close()
        asyncio.run(fetch_status())

if __name__ == "__main__":
    main()
