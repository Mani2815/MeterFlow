# Dataset Lineage Audit

## Overview
This document traces the data lineage from the official UK Power Networks SmartMeter dataset to its current destination in the Utility Meter-to-Cash Cloud Data Platform.

## Lineage Path

### 1. Official Source
- **Actual Source**: London Datastore - SmartMeter Energy Consumption Data in London Households
- **Actual URL**: `https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d`
- **Resource Name**: `Partitioned_LCL_Data.zip` (Contains 168 CSVs)
- **Format**: CSV in ZIP

### 2. HTTP Download & Ingestion (Raw Layer)
- **Component**: `backend/app/ingestion/smartmeter.py`
- **Process**: Streams the ZIP file from the London Datastore directly, extracts chunks, parses the CSV dynamically, maps the columns, and adds `source_system` and derived `meter_id`.
- **Actual Storage Location**: Local mock GCS bucket at `/tmp/mock_gcs/utility/raw/smartmeter/Small LCL Data/LCL-June2015v2_0.csv/run=<id>/`
- **Format**: NDJSON

### 3. Standardization (Standardized / Silver Layer)
- **Component**: `backend/app/processing/standardize.py`
- **Process**: Reads NDJSON chunks into a pandas DataFrame, coerces data types (e.g., timestamps to UTC, consumption to numeric), adds audit columns (`processed_at`, `ingestion_run_id`, `standardize_run_id`).
- **Actual Storage Location**: `/tmp/mock_gcs/utility/standardized/smartmeter/run_<id>.parquet`
- **Format**: Snappy-compressed Parquet

### 4. Validation (Gold Layer / DLQ)
- **Component**: `backend/app/processing/quality.py`
- **Process**: Reads Standardized Parquet, applies Data Quality rules (Completeness, Validity, Uniqueness). Valid records are written out, invalid records are dropped and logged to `dlq_event` PostgreSQL table.
- **Actual Storage Location (Valid)**: `/tmp/mock_gcs/utility/gold/smartmeter/gold_<id>.parquet`
- **Actual Storage Location (Invalid)**: PostgreSQL `dlq_event` table.

### 5. Data Warehouse (BigQuery)
- **Component**: Missing
- **Status**: GAP IDENTIFIED. The pipeline currently terminates at the Gold Parquet zone. There is no automated load into BigQuery or PostgreSQL Analytics table yet.

### 6. Analytics & Frontend
- **Component**: `ui/src/app/console/page.tsx`, `ui/src/components/landing/StatusStrip.tsx`, `backend/app/main.py`
- **Process**: The UI polls the dashboard API, which fetches `IngestionRun` and `DataQualityRun` stats from PostgreSQL to populate the dashboard metrics.
- **Status**: The backend reads metadata about the pipelines, but the raw meter reads are NOT queried because they are not yet in BigQuery or a relational database for Analytics consumption. 

## Unexplained Gaps
- **Warehouse Gap**: The Parquet files in the Gold zone are not loaded into BigQuery. Therefore, analytic queries against consumption data are not possible yet.
- **Frontend Usage Gap**: While pipeline metadata (rows processed, quality score) is perfectly wired end-to-end, the actual consumption readings (the data itself) are not displayed on the UI. The "Consumption chart" in the Overview page still uses a static `chartData` array (`ui/src/app/console/page.tsx`).

## Column-Level Mapping & Lineage
| Target Schema Phase | Field | Source | Note |
| :--- | :--- | :--- | :--- |
| **Source-derived** | `stdorToU` | `Partitioned_LCL_Data.zip` | Captured as is during Raw ingestion |
| **Derived** | `stdor_to_u` | `stdorToU` | Renamed in Standardized / Gold zone |
| **Derived** | `dim_tariff.source_tariff_code` | `stdor_to_u` | Mapped in BigQuery warehouse schema |
