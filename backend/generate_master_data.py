import argparse
import glob
import os
import random
import pandas as pd
from datetime import datetime

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.master_data import SyntheticCustomer, SyntheticAccount, SyntheticServicePoint, SyntheticContract, SyntheticMeter

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://meter:meterpass@db:5432/meter_db")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

def get_unique_households():
    """Extract distinct real UKPN households and their tariffs from Gold dataset."""
    storage_dir = os.getenv("STORAGE_DIR", "/tmp/mock_gcs")
    gold_dir = f"{storage_dir}/utility/gold/smartmeter/"
    files = glob.glob(os.path.join(gold_dir, "*.parquet"))
    if not files:
        print("No Gold Parquet files found. Run the ingestion pipeline first.")
        return pd.DataFrame()
        
    latest_file = max(files, key=os.path.getctime)
    df = pd.read_parquet(latest_file)
    
    # We want unique household_id and its associated tariff
    # Since a household should have one tariff, we just drop duplicates
    df_unique = df[['household_id', 'stdor_to_u']].drop_duplicates(subset=['household_id'])
    return df_unique

async def generate_master_data(seed: int):
    random.seed(seed)
    
    df_source = get_unique_households()
    if df_source.empty:
        return
        
    customers = []
    accounts = []
    service_points = []
    contracts = []
    meters = []
    
    # Deterministic generation
    for _, row in df_source.iterrows():
        hh_id = row['household_id']
        tariff = row['stdor_to_u']
        
        # We know hh_id is like "MAC000002"
        # Extract the suffix for clean synthetic IDs
        suffix = hh_id.replace("MAC", "")
        
        c_id = f"CUS-{suffix}"
        a_id = f"ACC-{suffix}"
        sp_id = f"SP-{suffix}"
        ctr_id = f"CTR-{suffix}"
        m_id = f"METER-{suffix}"
        
        # 1. Customer
        customers.append({
            "id": c_id,
            "status": "ACTIVE",
            "created_at": datetime(2010, 1, 1)
        })
        
        # 2. Account
        accounts.append({
            "id": a_id,
            "customer_id": c_id,
            "status": "ACTIVE",
            "opened_at": datetime(2010, 1, 15),
            "currency": "GBP"
        })
        
        # 3. Service Point
        service_points.append({
            "id": sp_id,
            "region_code": "REGION-LONDON",
            "status": "ACTIVE"
        })
        
        # 4. Contract
        contracts.append({
            "id": ctr_id,
            "account_id": a_id,
            "service_point_id": sp_id,
            "status": "ACTIVE",
            "contract_start": datetime(2010, 1, 20),
            "contract_end": None
        })
        
        # 5. Meter
        meters.append({
            "id": m_id,
            "source_household_id": hh_id,
            "service_point_id": sp_id,
            "tariff_code": tariff,
            "meter_type": "SMART_ELECTRICITY",
            "installation_date": datetime(2010, 2, 1),
            "status": "ACTIVE"
        })
        
    # Convert to DataFrames
    df_customers = pd.DataFrame(customers)
    df_accounts = pd.DataFrame(accounts)
    df_service_points = pd.DataFrame(service_points)
    df_contracts = pd.DataFrame(contracts)
    df_meters = pd.DataFrame(meters)
    
    # Save to Synthetic Data Lake
    storage_dir = os.getenv("STORAGE_DIR", "/tmp/mock_gcs")
    base_dir = f"{storage_dir}/synthetic"
    
    for name, df in [
        ("customer", df_customers),
        ("account", df_accounts),
        ("service_point", df_service_points),
        ("contract", df_contracts),
        ("meter", df_meters)
    ]:
        out_dir = os.path.join(base_dir, name)
        os.makedirs(out_dir, exist_ok=True)
        
        pq_path = os.path.join(out_dir, f"{name}.parquet")
        csv_path = os.path.join(out_dir, f"{name}.csv")
        
        df.to_parquet(pq_path, compression="snappy")
        df.to_csv(csv_path, index=False)
        print(f"Exported {len(df)} records to {pq_path}")
        
    # Load to DB
    print("Loading to PostgreSQL...")
    db = AsyncSessionLocal()
    
    try:
        from sqlalchemy import delete
        
        # Clear existing data to allow reproducible runs
        await db.execute(delete(SyntheticMeter))
        await db.execute(delete(SyntheticContract))
        await db.execute(delete(SyntheticServicePoint))
        await db.execute(delete(SyntheticAccount))
        await db.execute(delete(SyntheticCustomer))
        await db.commit()
        
        # Insert
        for c in customers: db.add(SyntheticCustomer(**c))
        for a in accounts: db.add(SyntheticAccount(**a))
        for sp in service_points: db.add(SyntheticServicePoint(**sp))
        for ctr in contracts: db.add(SyntheticContract(**ctr))
        for m in meters: db.add(SyntheticMeter(**m))
        
        await db.commit()
        print("Database load successful.")
    except Exception as e:
        await db.rollback()
        print(f"Failed to load DB: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    args = parser.parse_args()
    
    asyncio.run(generate_master_data(args.seed))
