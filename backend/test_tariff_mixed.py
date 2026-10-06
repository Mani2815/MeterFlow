import asyncio
import os
import uuid
import pandas as pd
import zipfile
import io

from app.ingestion.smartmeter import process_csv_file, record_run
from app.processing.standardize import standardize_smartmeter, AsyncSessionLocal
from app.processing.quality import run_data_quality
from app.models.core import StandardizeRun

async def prepare_mixed_csv():
    zip_path = "/tmp/Partitioned_LCL_Data.zip"
    print("Extracting mixed dataset...")
    with zipfile.ZipFile(zip_path, "r") as z:
        # Get 500 Std
        with z.open("Small LCL Data/LCL-June2015v2_0.csv") as f:
            df_std = pd.read_csv(f).head(500)
        # Get 500 ToU
        with z.open("Small LCL Data/LCL-June2015v2_160.csv") as f:
            df_tou = pd.read_csv(f).head(500)
            
    df_mixed = pd.concat([df_std, df_tou], ignore_index=True)
    # Save to memory buffer
    csv_buffer = io.StringIO()
    df_mixed.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    return csv_buffer, len(df_std), len(df_tou)

async def run_pipeline():
    csv_buffer, num_std, num_tou = await prepare_mixed_csv()
    
    print(f"Prepared Source Dataset: {num_std} Std, {num_tou} ToU")
    
    # 1. Ingest
    ingest_run_id = str(uuid.uuid4())
    print(f"Testing Ingestion (Run ID: {ingest_run_id})...")
    # Wrap in BytesIO for TextIOWrapper which expects binary
    bytes_buffer = io.BytesIO(csv_buffer.getvalue().encode('utf-8'))
    process_csv_file(bytes_buffer, "mixed_tariffs_test.csv", ingest_run_id, "test")
    
    db = AsyncSessionLocal()
    await record_run(db, ingest_run_id, "mixed_tariffs_test.csv", "SUCCESS", 1000, 100000)
    await db.commit()
    
    # 2. Standardize
    print("Testing Standardization...")
    await standardize_smartmeter(ingest_run_id)
    
    # find latest standardize run
    from sqlalchemy.future import select
    result = await db.execute(select(StandardizeRun).where(StandardizeRun.ingestion_run_id == ingest_run_id).order_by(StandardizeRun.started_at.desc()))
    std_run = result.scalars().first()
    std_run_id = std_run.run_id
    print(f"Standardize Run ID: {std_run_id}")
    
    # 3. Quality
    print("Testing Quality...")
    await run_data_quality(std_run_id)
    await db.close()
    
    print("Pipeline finished.")
    
    # 4. Verify outputs
    import glob
    raw_files = glob.glob(f"/tmp/mock_gcs/utility/raw/smartmeter/mixed_tariffs_test.csv/run={ingest_run_id}/*.json", recursive=True)
    if raw_files:
        df_raw = pd.read_json(raw_files[0], lines=True)
        print("--- RAW STAGE ---")
        print("Rows:", len(df_raw))
        print("Value counts:\n", df_raw.get('stdorToU', pd.Series()).value_counts(dropna=False))
        
    std_file = f"/tmp/mock_gcs/utility/standardized/smartmeter/run_{ingest_run_id}.parquet"
    if os.path.exists(std_file):
        df_std = pd.read_parquet(std_file)
        print("--- STANDARDIZED STAGE ---")
        print("Rows:", len(df_std))
        print("Value counts:\n", df_std.get('stdor_to_u', pd.Series()).value_counts(dropna=False))
        
    gold_file = f"/tmp/mock_gcs/utility/gold/smartmeter/gold_{std_run_id}.parquet"
    if os.path.exists(gold_file):
        df_gold = pd.read_parquet(gold_file)
        print("--- GOLD STAGE ---")
        print("Rows:", len(df_gold))
        print("Value counts:\n", df_gold.get('stdor_to_u', pd.Series()).value_counts(dropna=False))

if __name__ == "__main__":
    asyncio.run(run_pipeline())
