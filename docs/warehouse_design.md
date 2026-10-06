# Phase 5: BigQuery Analytical Warehouse Design

## 1. Layers

The data warehouse follows a medallion-like 3-tier architecture:
- **Staging (`meter_to_cash_stg`)**: Contains views or transient tables that parse the JSON payloads extracted during Phase 2 (Batch) and Phase 4 (CDC). Deduplicates raw records using `QUALIFY ROW_NUMBER()`.
- **Core (`meter_to_cash_core`)**: The central Star Schema. Houses the conformed Dimensions and Facts.
- **Marts (`meter_to_cash_marts`)**: Aggregated analytical tables built on top of the Core layer (e.g., Monthly Revenue, Daily Consumption).

## 2. Dimensional Model (Star Schema)

### Dimensions (SCD Type 1 & 2)
- `dim_customer`: One row per customer. (SCD1 for this phase).
- `dim_account`: One row per account.
- `dim_contract`: One row per service agreement.
- `dim_location`: One row per physical premise.
- `dim_service_point`: One row per delivery point.
- `dim_meter`: One row per meter. Contains `installation_date` and `decommission_date` representing meter lifecycle.
- `dim_date`: Standard calendar dimension to allow slicing metrics by day/month/quarter/year.

### Facts
- `fact_meter_reading`: 
  - **Grain**: One row per distinct reading event from a meter.
  - **Why it exists**: Tracks the lowest-grain telemetry payload.
- `fact_billing`:
  - **Grain**: One row per bill issued to an account.
  - **Why it exists**: Tracks revenue and outstanding debt lifecycle.
- `fact_payment`:
  - **Grain**: One row per payment transaction applied to a bill.
  - **Why it exists**: Tracks collected cash.
- `fact_consumption`:
  - **Grain**: One row per contract, per billing period usage.
  - **Why it exists**: Extracted from bill usage amounts to track billed consumption separately from raw telemetry.

## 3. Physical Design

### Surrogate Keys
Instead of heavy auto-incrementing sequences, we use deterministic hashing for Surrogate Keys (SK). 
```sql
FARM_FINGERPRINT(CAST(natural_key AS STRING)) AS customer_sk
```
This enables parallel, independent dimension generation and allows fact tables to generate the SKs on the fly during loads without massive JOINs back to the dimension tables.

### Partitioning Strategy
- Facts are partitioned by their primary temporal event:
  - `fact_meter_reading`: Partitioned by `read_at` (DAY).
  - `fact_billing`: Partitioned by `bill_date` (MONTH).
  - `fact_payment`: Partitioned by `payment_date` (MONTH).

### Clustering Strategy
- Dimensions are clustered by their SKs and natural keys.
- Facts are clustered by their highest-cardinality foreign keys used in filtering (e.g., `account_sk`, `meter_sk`).

## 4. Incremental Processing Strategy
We utilize BigQuery `MERGE` statements to idempotently upsert data.
- **Handling Duplicates**: In the staging views, we use window functions: 
  `QUALIFY ROW_NUMBER() OVER(PARTITION BY id ORDER BY ingestion_timestamp DESC) = 1`
  This ensures only the latest state of a CDC record enters the `MERGE`.
- **Handling Late Arriving Data**: The `MERGE` logic matches on the natural key. If a record arrives late but its `event_timestamp` is older than what's already in the Core table, the update is ignored.
- **Audit Columns**: 
  - `bq_insert_timestamp`: When the row first entered the warehouse.
  - `bq_update_timestamp`: When the row was last modified via CDC.
  - `source_system`: Defines the origin (e.g., `cdc_datastream` vs `batch_ingestion`).
