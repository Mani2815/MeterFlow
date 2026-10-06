import asyncio
import os
import uuid
import pandas as pd
from app.ingestion.smartmeter import run_ingestion
from app.processing.standardize import standardize_smartmeter
from app.processing.quality import run_data_quality

async def run_pipeline():
    # 1. Ingest
    target_files = ["1"]
    # We will trigger the API or just run the functions
    print("Testing Ingestion...")
    # Actually, `run_ingestion` does not return the run_id, let's just find the latest directory in mock GCS
    await run_ingestion(target_files, "test")
    
    # Wait a bit or fetch the run_id from DB
    from app.processing.standardize import AsyncSessionLocal
    from app.models.core import IngestionRun, StandardizeRun
    from sqlalchemy.future import select
    db = AsyncSessionLocal()
    # find latest ingestion
    result = await db.execute(select(IngestionRun).order_by(IngestionRun.started_at.desc()))
    ingest_run = result.scalars().first()
    ingest_run_id = ingest_run.run_id
    print(f"Ingestion Run ID: {ingest_run_id}")
    
    # 2. Standardize
    print("Testing Standardization...")
    await standardize_smartmeter(ingest_run_id)
    
    # find latest standardize run
    result = await db.execute(select(StandardizeRun).where(StandardizeRun.ingestion_run_id == ingest_run_id).order_by(StandardizeRun.started_at.desc()))
    std_run = result.scalars().first()
    std_run_id = std_run.run_id
    print(f"Standardize Run ID: {std_run_id}")
    
    # 3. Quality
    print("Testing Quality...")
    await run_data_quality(std_run_id)
    
    print("Pipeline finished.")
    
    # 4. Verify outputs
    import glob
    raw_files = glob.glob(f"/tmp/mock_gcs/utility/raw/smartmeter/**/run={ingest_run_id}/*.json", recursive=True)
    if raw_files:
        df_raw = pd.read_json(raw_files[0], lines=True)
        print("Raw Columns:", list(df_raw.columns))
        print("Raw stdorToU value counts:\n", df_raw.get('stdorToU', pd.Series()).value_counts(dropna=False))
        
    std_file = f"/tmp/mock_gcs/utility/standardized/smartmeter/run_{ingest_run_id}.parquet"
    if os.path.exists(std_file):
        df_std = pd.read_parquet(std_file)
        print("Std Columns:", list(df_std.columns))
        print("Std stdor_to_u value counts:\n", df_std.get('stdor_to_u', pd.Series()).value_counts(dropna=False))
        
    gold_file = f"/tmp/mock_gcs/utility/gold/smartmeter/gold_{std_run_id}.parquet"
    if os.path.exists(gold_file):
        df_gold = pd.read_parquet(gold_file)
        print("Gold Columns:", list(df_gold.columns))
        print("Gold stdor_to_u value counts:\n", df_gold.get('stdor_to_u', pd.Series()).value_counts(dropna=False))

if __name__ == "__main__":
    asyncio.run(run_pipeline())
