# Source Schema Validation

## Overview
This document compares the official London Datastore UK Power Networks SmartMeter dataset schema against the project's Raw and Canonical (Standardized) schemas.

## Schema Mapping

| SOURCE COLUMN | RAW COLUMN | CANONICAL COLUMN | WAREHOUSE COLUMN | NOTES |
| :--- | :--- | :--- | :--- | :--- |
| `LCLid` | `household_id` | `household_id` | N/A | Kept as string (e.g. `MAC000002`) |
| `LCLid` | `meter_id` | `meter_id` | N/A | **DERIVED**: The project extracts the numeric portion of `LCLid` and prefixes it with `METER-`. E.g., `MAC000002` → `METER-000002`. |
| `stdorToU` | N/A | N/A | N/A | **DROPPED**: The tariff type (Standard or Time-of-Use) is currently ignored and dropped by the ingestion pipeline. |
| `DateTime` | `event_timestamp` | `event_timestamp` | N/A | Renamed and cast to UTC datetime. |
| `KWH/hh (per half hour) ` | `consumption_kwh` | `consumption_kwh` | N/A | Renamed, cleaned of trailing whitespace, and cast to numeric float. Nulls/errors coerced to 0.0 during standardization. |
| N/A | `source_system` | `source_system` | N/A | **DERIVED**: Hardcoded as `uk_power_networks`. |
| N/A | N/A | `processed_at` | N/A | **DERIVED**: Auditing timestamp added during standardization. |
| N/A | N/A | `ingestion_run_id` | N/A | **DERIVED**: Auditing foreign key added during standardization. |
| N/A | N/A | `standardize_run_id` | N/A | **DERIVED**: Auditing primary key added during standardization. |

## Data Type Validations
- `household_id`: Preserved as string, maps 1:1 with source.
- `meter_id`: Derived as string, deterministic 1:1 mapping mapping from `household_id`.
- `event_timestamp`: Successfully parsed as timestamp with timezone (UTC).
- `consumption_kwh`: Numeric cast works, but `errors='coerce'` converts "Null" strings in the source to `NaN`, which is then filled with `0.0`. This is potentially dangerous if missing intervals should be treated as `NULL` instead of `0`.

## Gaps
- The `stdorToU` tariff column is completely ignored, meaning tariff-based billing logic cannot be accurately implemented later without it.
- The Warehouse column is marked N/A because there is no BigQuery / Data Warehouse target implemented yet.
