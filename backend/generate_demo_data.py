#!/usr/bin/env python3
"""
generate_demo_data.py

Reads the validated Gold Parquet output and generates compact JSON snapshots
for the frontend Vercel deployment.

Usage:
    python scripts/generate_demo_data.py

Output:
    ui/public/data/
        dataset-summary.json
        tariff-distribution.json
        daily-consumption.json
        pipeline-summary.json
        data-quality.json
        schema.json
"""

import glob
import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

GOLD_DIR = "/tmp/mock_gcs/utility/gold/smartmeter/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "ui", "public", "data")
GENERATED_AT = datetime.now(timezone.utc).isoformat()


def load_gold() -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(GOLD_DIR, "*.parquet")))
    if not files:
        print(f"ERROR: No Parquet files found in {GOLD_DIR}")
        print("Run the ingestion pipeline first (see README).")
        sys.exit(1)
    print(f"Found {len(files)} Gold Parquet file(s). Reading latest...")
    # Use the most recent file
    latest = max(files, key=os.path.getctime)
    df = pd.read_parquet(latest)
    print(f"Loaded {len(df):,} rows from {os.path.basename(latest)}")
    return df, latest


def save(filename: str, data: dict | list):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  Wrote {filename}")


def generate_dataset_summary(df: pd.DataFrame, source_file: str):
    tariff_counts = {}
    if "stdor_to_u" in df.columns:
        tariff_counts = df["stdor_to_u"].value_counts().to_dict()

    try:
        min_ts = str(df["event_timestamp"].min())
        max_ts = str(df["event_timestamp"].max())
    except Exception:
        min_ts = None
        max_ts = None

    total_kwh = float(df["consumption_kwh"].sum()) if "consumption_kwh" in df.columns else 0.0

    data = {
        "generated_at": GENERATED_AT,
        "source": "UK Power Networks — SmartMeter Energy Consumption Data in London Households",
        "source_url": "https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d",
        "gold_file": os.path.basename(source_file),
        "storage_zone": "Gold (Parquet)",
        "total_rows": len(df),
        "distinct_households": int(df["household_id"].nunique()) if "household_id" in df.columns else 0,
        "total_consumption_kwh": round(total_kwh, 4),
        "tariff_std_count": int(tariff_counts.get("Std", 0)),
        "tariff_tou_count": int(tariff_counts.get("ToU", 0)),
        "date_range": {"from": min_ts, "to": max_ts},
        "columns": list(df.columns),
    }
    save("dataset-summary.json", data)
    return data


def generate_tariff_distribution(df: pd.DataFrame):
    if "stdor_to_u" not in df.columns:
        save("tariff-distribution.json", [])
        return

    counts = df["stdor_to_u"].value_counts()
    total = counts.sum()
    data = [
        {
            "tariff": name,
            "count": int(count),
            "pct": round(float(count) / total * 100, 1),
        }
        for name, count in counts.items()
    ]
    save("tariff-distribution.json", {"generated_at": GENERATED_AT, "distribution": data})


def generate_daily_consumption(df: pd.DataFrame):
    if "event_timestamp" not in df.columns or "consumption_kwh" not in df.columns:
        save("daily-consumption.json", [])
        return

    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["event_timestamp"], utc=True).dt.date
    daily = (
        df2.groupby("date")["consumption_kwh"]
        .agg(total_kwh="sum", reading_count="count")
        .reset_index()
        .sort_values("date")
    )
    data = [
        {
            "date": str(row["date"]),
            "total_kwh": round(float(row["total_kwh"]), 4),
            "reading_count": int(row["reading_count"]),
        }
        for _, row in daily.iterrows()
    ]
    save("daily-consumption.json", {"generated_at": GENERATED_AT, "daily": data})


def generate_pipeline_summary(df: pd.DataFrame):
    """
    Builds pipeline stage summary from the data we can infer from the Gold file.
    The actual run counts come from gold row counts; we document the stages.
    """
    gold_rows = len(df)

    data = {
        "generated_at": GENERATED_AT,
        "note": "Snapshot generated from validated Gold dataset. Not a live backend query.",
        "stages": [
            {
                "name": "UKPN Source",
                "status": "ACTIVE",
                "description": "SmartMeter Energy Consumption Data in London Households (168 CSV files)",
                "format": "CSV (ZIP archive)",
                "rows": None,
            },
            {
                "name": "Raw",
                "status": "PASS",
                "description": "Ingested to Raw zone as NDJSON",
                "format": "NDJSON",
                "fields": ["meter_id", "household_id", "event_timestamp", "consumption_kwh", "stdorToU", "source_system"],
                "rows": gold_rows,  # lower bound — we only have gold count
            },
            {
                "name": "Standardized",
                "status": "PASS",
                "description": "Renamed fields, added provenance metadata, wrote Parquet",
                "format": "Parquet (Snappy)",
                "fields": ["meter_id", "household_id", "event_timestamp", "consumption_kwh", "stdor_to_u", "processed_at", "ingestion_run_id"],
                "rows": gold_rows,
            },
            {
                "name": "Gold",
                "status": "PASS",
                "description": "Validated, deduplicated, DQ-checked records",
                "format": "Parquet (Snappy)",
                "fields": ["meter_id", "household_id", "event_timestamp", "consumption_kwh", "stdor_to_u", "standardize_run_id"],
                "rows": gold_rows,
            },
            {
                "name": "BigQuery",
                "status": "BLOCKED",
                "description": "GCP Application Default Credentials not configured. Schema is defined and ready.",
                "rows": None,
            },
        ],
    }
    save("pipeline-summary.json", data)


def generate_data_quality(df: pd.DataFrame):
    total = len(df)
    null_tariff = int(df["stdor_to_u"].isna().sum()) if "stdor_to_u" in df.columns else 0
    null_kwh = int(df["consumption_kwh"].isna().sum()) if "consumption_kwh" in df.columns else 0
    dup_count = int(df.duplicated().sum())

    valid = total - null_tariff - null_kwh - dup_count
    quality_score = round(valid / total * 100, 1) if total > 0 else 0

    data = {
        "generated_at": GENERATED_AT,
        "source": "Gold Parquet zone",
        "total_rows": total,
        "valid_rows": max(valid, 0),
        "null_tariff": null_tariff,
        "null_kwh": null_kwh,
        "duplicates": dup_count,
        "quality_score": quality_score,
        "dimensions": {
            "completeness": round((1 - null_kwh / total) * 100, 1) if total > 0 else 100,
            "validity": round((1 - null_tariff / total) * 100, 1) if total > 0 else 100,
            "uniqueness": round((1 - dup_count / total) * 100, 1) if total > 0 else 100,
        },
    }
    save("data-quality.json", data)


def generate_schema():
    data = {
        "generated_at": GENERATED_AT,
        "table": "gold/smartmeter/gold_*.parquet",
        "description": "UKPN SmartMeter Gold zone — one row per validated meter reading event",
        "columns": [
            {"name": "meter_id", "type": "STRING", "nullable": False, "origin": "Derived", "description": "Synthetic meter ID (METER- prefix + LCLid suffix)"},
            {"name": "household_id", "type": "STRING", "nullable": False, "origin": "UKPN (Real)", "description": "LCLid — real source household identifier from UKPN dataset"},
            {"name": "event_timestamp", "type": "TIMESTAMP", "nullable": False, "origin": "UKPN (Real)", "description": "DateTime of the half-hour reading interval (UTC)"},
            {"name": "consumption_kwh", "type": "FLOAT64", "nullable": True, "origin": "UKPN (Real)", "description": "Electricity consumption in kWh for the half-hour interval"},
            {"name": "stdor_to_u", "type": "STRING", "nullable": True, "origin": "UKPN (Real)", "description": "Tariff classification: Std (Standard) or ToU (Time of Use). Preserved exactly from source stdorToU field."},
            {"name": "source_system", "type": "STRING", "nullable": False, "origin": "System", "description": "Always: uk_power_networks"},
            {"name": "processed_at", "type": "TIMESTAMP", "nullable": False, "origin": "System", "description": "Timestamp when standardization was applied"},
            {"name": "ingestion_run_id", "type": "STRING", "nullable": False, "origin": "System", "description": "Reference to the IngestionRun that produced this record"},
            {"name": "standardize_run_id", "type": "STRING", "nullable": False, "origin": "System", "description": "Reference to the StandardizeRun that produced this record"},
        ],
    }
    save("schema.json", data)


def main():
    print("=" * 60)
    print("Gold → Demo Data Snapshot Generator")
    print("=" * 60)

    df, source_file = load_gold()

    print("\nGenerating snapshots...")
    summary = generate_dataset_summary(df, source_file)
    generate_tariff_distribution(df)
    generate_daily_consumption(df)
    generate_pipeline_summary(df)
    generate_data_quality(df)
    generate_schema()

    print(f"\nOutput directory: {os.path.abspath(OUTPUT_DIR)}")
    print("\nSummary of generated data:")
    print(f"  Total rows:          {summary['total_rows']:,}")
    print(f"  Distinct households: {summary['distinct_households']:,}")
    print(f"  Tariff Std:          {summary['tariff_std_count']:,}")
    print(f"  Tariff ToU:          {summary['tariff_tou_count']:,}")
    print(f"  Date range:          {summary['date_range']['from']} → {summary['date_range']['to']}")
    print("\nDone. Commit ui/public/data/ to your repository.")


if __name__ == "__main__":
    main()
