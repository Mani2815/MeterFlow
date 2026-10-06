# Gold to BigQuery Mapping

## Overview
This document outlines the mapping of the existing Gold Parquet data to the BigQuery analytical warehouse, as requested in Phase 1 & 2 of the Analytics Pipeline implementation.

## 1. Gold Parquet Schema & Location
- **Location**: `/tmp/mock_gcs/utility/gold/smartmeter/`
- **Format**: Parquet (Snappy compression)
- **Schema**:
  - `meter_id` (string)
  - `household_id` (string)
  - `event_timestamp` (datetime UTC)
  - `consumption_kwh` (float64)
  - `source_system` (string)
  - `processed_at` (datetime UTC)
  - `ingestion_run_id` (string)
  - `standardize_run_id` (string)
- **Row Count**: 999 valid rows (from the initial 1000 row test batch of the first UKPN dataset partition).
- **Duplicate Handling**: Duplicates are removed during the Quality stage (1 removed). 

## 2. BigQuery Data Model

### Fact Table: `fact_meter_reading`
- **Grain**: One row per half-hourly meter reading per household.
- **Partitioning**: Partitioned by DAY on `event_timestamp` for efficient time-series querying.
- **Clustering**: Clustered by `household_id` to speed up individual household aggregation.

| Gold Column | BigQuery Column | Data Type | Notes |
| :--- | :--- | :--- | :--- |
| `household_id` | `source_household_id` | STRING | Original UKPN LCLid |
| `meter_id` | `meter_id` | STRING | Derived mapping (`METER-{numeric}`) |
| `event_timestamp` | `reading_timestamp` | TIMESTAMP | Renamed for clarity |
| `consumption_kwh` | `consumption_kwh` | FLOAT64 | Cleaned numeric value |
| *missing* | `tariff_type` | STRING | Not currently available (dropped in ingestion) |
| `source_system` | `source_file` | STRING | Source identifier |
| `ingestion_run_id` | `ingestion_run_id` | STRING | Lineage tracking |
| `processed_at` | `ingestion_date` | TIMESTAMP | Lineage tracking |

### Dimensions
Since synthetic customer/billing data is strictly separated and not currently derived, we will only create dimensions naturally supported by the dataset:

#### `dim_meter`
- **Grain**: One row per unique meter.
- **Schema**:
  - `meter_id` (STRING)
  - `source_household_id` (STRING)
  - `first_reading_date` (TIMESTAMP)
  - `last_reading_date` (TIMESTAMP)

*(Note: `dim_tariff` cannot be built because `stdorToU` was dropped during ingestion. It will be addressed in a future task per instructions).*
