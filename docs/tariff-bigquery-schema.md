# BigQuery Tariff Schema & Dimension Design

## Overview
This document outlines the schema changes to BigQuery to support the preserved `stdorToU` tariff field.

## Fact Table Updates
The core fact table `fact_meter_reading` is updated to include the exact `stdor_to_u` string.

```sql
CREATE TABLE IF NOT EXISTS `utility_analytics.fact_meter_reading` (
    source_household_id STRING,
    meter_id STRING,
    reading_timestamp TIMESTAMP,
    consumption_kwh FLOAT64,
    stdor_to_u STRING,
    source_system STRING,
    ingestion_date TIMESTAMP,
    ingestion_run_id STRING,
    standardize_run_id STRING
)
PARTITION BY DATE(reading_timestamp)
CLUSTER BY source_household_id;
```

## Tariff Dimension (`dim_tariff`)
Based on Phase 9 instructions, the dimension must strictly reflect actual observed categories without inventing prices.

### Schema Definition
```sql
CREATE TABLE IF NOT EXISTS `utility_analytics.dim_tariff` (
    tariff_key STRING,                 -- e.g. "UKPN-STD"
    source_tariff_code STRING,         -- The exact stdorToU value (e.g. "Std", "ToU")
    tariff_description STRING,         -- Human readable mapped description
    source_system STRING,              -- e.g. "uk_power_networks"
    valid_from TIMESTAMP,              
    valid_to TIMESTAMP                 
);
```

### Initial Data Load
Because there is no external metadata providing actual pricing, the dimension only describes the classification type:

```sql
INSERT INTO `utility_analytics.dim_tariff` (
    tariff_key, source_tariff_code, tariff_description, source_system, valid_from, valid_to
)
VALUES 
    ('UKPN-STD', 'Std', 'Standard Tariff (Flat Rate)', 'uk_power_networks', '2010-01-01', NULL),
    ('UKPN-TOU', 'ToU', 'Time of Use Tariff (Variable Rate)', 'uk_power_networks', '2010-01-01', NULL);
```

### Status
- **Schema Defined**: Yes
- **Loader Updated**: Yes (in `bq_loader.py`)
- **Execution**: **BLOCKED** due to lack of GCP Application Default Credentials in the container. No actual BigQuery tables have been created or modified.
