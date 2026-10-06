import os
import zipfile
import pandas as pd
import json

def audit():
    zip_path = "/tmp/Partitioned_LCL_Data.zip"
    if not os.path.exists(zip_path):
        print(f"ZIP file not found at {zip_path}")
        return

    # Verify ZIP content
    with zipfile.ZipFile(zip_path, 'r') as z:
        files = z.namelist()
        print(f"Total files in ZIP: {len(files)}")
        csv_files = [f for f in files if f.endswith('.csv')]
        print(f"Total CSV files: {len(csv_files)}")
        
        # Look at the first CSV
        first_csv = csv_files[0]
        with z.open(first_csv) as f:
            df_source = pd.read_csv(f, nrows=2000)
            print(f"\n--- SOURCE ({first_csv}) ---")
            print(f"Source Columns: {list(df_source.columns)}")
            print(f"Rows read: {len(df_source)}")
            print("Sample head:")
            print(df_source.head(2))

    # Raw layer
    import glob
    raw_files = glob.glob("/tmp/mock_gcs/utility/raw/smartmeter/**/*.json", recursive=True)
    print(f"\n--- RAW LAYER ---")
    print(f"Raw JSON chunks found: {len(raw_files)}")
    if raw_files:
        df_raw = pd.read_json(raw_files[0], lines=True)
        print(f"Raw Columns: {list(df_raw.columns)}")
        print(f"Rows in first chunk: {len(df_raw)}")
        print("Sample head:")
        print(df_raw.head(2))

    # Standardized layer
    std_files = glob.glob("/tmp/mock_gcs/utility/standardized/smartmeter/*.parquet")
    print(f"\n--- STANDARDIZED LAYER ---")
    print(f"Standardized Parquet found: {len(std_files)}")
    if std_files:
        df_std = pd.read_parquet(std_files[0])
        print(f"Standardized Columns: {list(df_std.columns)}")
        print(f"Rows in standardized: {len(df_std)}")

    # Gold layer
    gold_files = glob.glob("/tmp/mock_gcs/utility/gold/smartmeter/*.parquet")
    print(f"\n--- GOLD LAYER ---")
    print(f"Gold Parquet found: {len(gold_files)}")
    if gold_files:
        df_gold = pd.read_parquet(gold_files[0])
        print(f"Gold Columns: {list(df_gold.columns)}")
        print(f"Rows in gold: {len(df_gold)}")
        print("Sample head:")
        print(df_gold.head(2))
        
        # Stats on gold
        print("\n--- GOLD STATS ---")
        print(f"Min timestamp: {df_gold['event_timestamp'].min()}")
        print(f"Max timestamp: {df_gold['event_timestamp'].max()}")
        print(f"Distinct households: {df_gold['household_id'].nunique()}")
        print(f"Min consumption: {df_gold['consumption_kwh'].min()}")
        print(f"Max consumption: {df_gold['consumption_kwh'].max()}")

if __name__ == "__main__":
    audit()
