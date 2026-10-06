# BigQuery Analytical Warehouse Design

## Architecture Layers
The data warehouse follows a medallion-like architecture adapted for BigQuery:
1. **Staging (Raw/Bronze)**: Contains raw data replicated directly from source systems (e.g., via Datastream or batch loads). Data is kept in its original format.
2. **Core (Silver/Gold)**: The central dimensional model (Star Schema). Contains cleansed, conformed Dimensions and Facts with surrogate keys, standardized data types, and audit columns.
3. **Marts (Platinum)**: Highly aggregated, business-specific views built on top of the Core layer (e.g., monthly revenue rollups).

## Star Schema & Grain Definition

### Dimensions
Dimensions provide the descriptive context for business processes.
- **`dim_customer`**: Grain = 1 row per unique customer entity. Tracks customer demographics and contact info.
- **`dim_account`**: Grain = 1 row per financial account. Represents the billing entity tied to a customer.
- **`dim_contract`**: Grain = 1 row per active/historical utility service contract linking an account to a service point.
- **`dim_meter`**: Grain = 1 row per physical meter asset. Tracks meter specifications and installation status.
- **`dim_service_point`**: Grain = 1 row per physical location where service is delivered.
- **`dim_location`**: Grain = 1 row per geographic/postal boundary (City, Zip Code, Region) for spatial analytics.
- **`dim_date`**: Standard calendar dimension (1 row per day).

### Facts
Facts store the quantitative measurements of business events.
- **`fact_meter_reading`**: Grain = 1 row per meter reading event. 
- **`fact_billing`**: Grain = 1 row per issued invoice/bill.
- **`fact_payment`**: Grain = 1 row per payment transaction received against an account.
- **`fact_consumption`**: Grain = 1 row per aggregated daily/hourly usage per meter (derived from raw readings).

## Data Modeling Standards
- **Surrogate Keys**: All core tables use a hashed surrogate key (e.g., `FARM_FINGERPRINT` of the natural key) to isolate the warehouse from source-system ID changes.
- **Audit Columns**: Every table includes:
  - `dw_created_at`: Timestamp when the record was first inserted into the warehouse.
  - `dw_updated_at`: Timestamp when the record was last updated.
  - `source_system`: Identifier of the origin system (e.g., 'postgres_ops').
- **Primary/Foreign Keys**: Documented logically via naming conventions (`_sk` suffix for surrogate keys). Note that BigQuery does not enforce foreign keys physically.

## Partitioning & Clustering Strategy
To optimize query performance and reduce BigQuery costs:
- **Fact Tables**: 
  - *Partitioned* by the primary event date (e.g., `reading_timestamp`, `issue_date`) truncated to DAY or MONTH depending on volume.
  - *Clustered* by foreign keys frequently used in filtering/joins (e.g., `meter_sk`, `account_sk`).
- **Dimension Tables**:
  - Generally not partitioned unless extremely large (e.g., `dim_customer` > 10M rows could be partitioned by ingestion date if history is tracked).
  - *Clustered* by commonly filtered attributes (e.g., `status`, `type`, `region`).

## Incremental Processing Strategy
- **MERGE (Upsert)**: All dimension and fact loads use the standard SQL `MERGE` statement.
- **Deduplication**: The `MERGE` logic relies on the natural key to match existing records. Using `ROW_NUMBER() OVER (PARTITION BY natural_key ORDER BY source_timestamp DESC)` ensures duplicate events in the source stream are resolved to the latest state before merging.
- **Late-Arriving Records**: Facts partitioned by event date naturally handle late-arriving records because the `MERGE` statement will route the data to the correct historical partition based on the event timestamp, avoiding full table scans.
