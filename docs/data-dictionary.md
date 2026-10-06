# Data Dictionary: Utility Meter-to-Cash Cloud Data Platform

This document defines every field across all three warehouse layers (raw, staging, warehouse)
and the marts layer, including data types, constraints, allowed values, and lineage.

---

## Conventions

| Symbol | Meaning |
|--------|---------|
| `PK` | Primary key |
| `FK` | Foreign key |
| `NN` | NOT NULL |
| `PII` | Personal Identifiable Information — pseudonymized in staging |
| `ENUM(...)` | Allowed values are restricted to the listed set |

All BigQuery tables include the following **platform-standard metadata columns** not repeated
in each table definition below:

| Column | Type | Present In | Description |
|--------|------|-----------|-------------|
| `_ingested_at` | TIMESTAMP | raw | Time the row landed in the raw BigQuery table |
| `_source_table` | STRING | raw | Source table/topic name (e.g., `public.customer`) |
| `_operation` | STRING | raw (CDC only) | `INSERT`, `UPDATE`, `DELETE` from Datastream |
| `_load_type` | STRING | raw | `INCREMENTAL` or `BACKFILL` |
| `_file_path` | STRING | raw (batch only) | GCS path of the source file |
| `dw_inserted_at` | TIMESTAMP | warehouse, marts | Time the row was first written to warehouse |
| `dw_updated_at` | TIMESTAMP | warehouse | Time the row was last modified in warehouse |

---

## 1. Customer

### `raw.customer`

| Column | BQ Type | Nullable | Source | Notes |
|--------|---------|----------|--------|-------|
| `customer_id` | STRING | NN | OLTP PK | UUID format |
| `first_name` | STRING | NN | OLTP | Raw PII — not masked |
| `last_name` | STRING | NN | OLTP | Raw PII — not masked |
| `email` | STRING | NN | OLTP | Raw PII |
| `phone` | STRING | YES | OLTP | Raw PII |
| `customer_type` | STRING | NN | OLTP | ENUM(RESIDENTIAL, COMMERCIAL, INDUSTRIAL) |
| `date_of_birth` | DATE | YES | OLTP | Raw PII |
| `created_at` | TIMESTAMP | NN | OLTP | |
| `updated_at` | TIMESTAMP | NN | OLTP | CDC watermark |

### `staging.customer`

| Column | BQ Type | Nullable | Transformation |
|--------|---------|----------|----------------|
| `customer_id` | STRING | NN | Pass-through |
| `first_name_hash` | STRING | NN | SHA-256 of `first_name` |
| `last_name_hash` | STRING | NN | SHA-256 of `last_name` |
| `email_hash` | STRING | NN | SHA-256 of `email` |
| `phone_hash` | STRING | YES | SHA-256 of `phone`, NULL if source NULL |
| `customer_type` | STRING | NN | UPPER(TRIM()) + ENUM validation |
| `date_of_birth_year` | INT64 | YES | EXTRACT(YEAR FROM date_of_birth) — year only, not full DOB |
| `created_at` | TIMESTAMP | NN | Pass-through |
| `updated_at` | TIMESTAMP | NN | Pass-through |
| `_staged_at` | TIMESTAMP | NN | CURRENT_TIMESTAMP() at staging job time |

### `warehouse.dim_customer`

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `customer_sk` | INT64 | NN PK | Auto-increment surrogate key |
| `customer_id` | STRING | NN | Natural key from OLTP |
| `first_name_hash` | STRING | NN | |
| `last_name_hash` | STRING | NN | |
| `email_hash` | STRING | NN | |
| `phone_hash` | STRING | YES | |
| `customer_type` | STRING | NN | |
| `date_of_birth_year` | INT64 | YES | |
| `valid_from` | TIMESTAMP | NN | SCD2 row effective start |
| `valid_to` | TIMESTAMP | YES | SCD2 row effective end; NULL = current |
| `is_current` | BOOL | NN | TRUE for the active version |
| `dw_inserted_at` | TIMESTAMP | NN | |
| `dw_updated_at` | TIMESTAMP | NN | |

---

## 2. Account

### `raw.account`

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `account_id` | STRING | NN | UUID |
| `customer_id` | STRING | NN | FK → Customer |
| `account_status` | STRING | NN | ENUM(ACTIVE, SUSPENDED, CLOSED) |
| `billing_cycle` | STRING | NN | ENUM(MONTHLY, QUARTERLY, ANNUAL) |
| `payment_method` | STRING | NN | ENUM(DIRECT_DEBIT, CREDIT_CARD, CHEQUE, BANK_TRANSFER) |
| `created_at` | TIMESTAMP | NN | |
| `updated_at` | TIMESTAMP | NN | CDC watermark |

### `staging.account` — same columns, types validated, UPPER/TRIM applied

### `warehouse.dim_account`

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `account_sk` | INT64 | NN PK | Surrogate key |
| `account_id` | STRING | NN | Natural key |
| `customer_id` | STRING | NN | FK (natural key, not SK) |
| `account_status` | STRING | NN | |
| `billing_cycle` | STRING | NN | |
| `payment_method` | STRING | NN | |
| `valid_from` | TIMESTAMP | NN | SCD2 |
| `valid_to` | TIMESTAMP | YES | SCD2 |
| `is_current` | BOOL | NN | |
| `dw_inserted_at` | TIMESTAMP | NN | |
| `dw_updated_at` | TIMESTAMP | NN | |

---

## 3. Contract

### `raw.contract`

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `contract_id` | STRING | NN | UUID |
| `account_id` | STRING | NN | FK → Account |
| `tariff_code` | STRING | NN | Free-text code, e.g. `RESI-FLAT-E1` |
| `commodity_type` | STRING | NN | ENUM(ELECTRICITY, GAS, WATER) |
| `start_date` | DATE | NN | |
| `end_date` | DATE | YES | NULL = open-ended |
| `contract_status` | STRING | NN | ENUM(ACTIVE, EXPIRED, TERMINATED) |
| `created_at` | TIMESTAMP | NN | |
| `updated_at` | TIMESTAMP | NN | CDC watermark |

### `warehouse.dim_contract` — SCD2 on `tariff_code`, `contract_status`

---

## 4. Service Point

### `raw.service_point`

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `service_point_id` | STRING | NN | UUID |
| `contract_id` | STRING | NN | FK → Contract |
| `address_line_1` | STRING | NN | |
| `address_line_2` | STRING | YES | |
| `city` | STRING | NN | |
| `state` | STRING | NN | |
| `postal_code` | STRING | NN | Stored as STRING to preserve leading zeros |
| `country` | STRING | NN | ISO 3166-1 alpha-2 (e.g., US) |
| `grid_zone` | STRING | YES | Distribution zone identifier |
| `created_at` | TIMESTAMP | NN | |
| `updated_at` | TIMESTAMP | NN | CDC watermark |

### `warehouse.dim_service_point` — SCD Type 1 (overwrite on address change)

---

## 5. Meter

### `raw.meter`

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `meter_id` | STRING | NN | UUID |
| `service_point_id` | STRING | NN | FK → Service Point |
| `meter_serial_number` | STRING | NN | Physical device serial; natural key for dedup |
| `meter_type` | STRING | NN | ENUM(AMI, AMR, MANUAL) |
| `commodity_type` | STRING | NN | ENUM(ELECTRICITY, GAS, WATER) |
| `status` | STRING | NN | ENUM(ACTIVE, INACTIVE, DECOMMISSIONED) |
| `installation_date` | DATE | NN | |
| `decommission_date` | DATE | YES | NULL if still active |
| `created_at` | TIMESTAMP | NN | |
| `updated_at` | TIMESTAMP | NN | CDC watermark |

### `warehouse.dim_meter` — SCD2 on `status`

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `meter_sk` | INT64 | NN PK | Surrogate key |
| `meter_id` | STRING | NN | Natural key |
| `service_point_id` | STRING | NN | |
| `meter_serial_number` | STRING | NN | |
| `meter_type` | STRING | NN | |
| `commodity_type` | STRING | NN | |
| `status` | STRING | NN | |
| `installation_date` | DATE | NN | |
| `decommission_date` | DATE | YES | |
| `valid_from` | TIMESTAMP | NN | SCD2 |
| `valid_to` | TIMESTAMP | YES | SCD2 |
| `is_current` | BOOL | NN | |
| `dw_inserted_at` | TIMESTAMP | NN | |
| `dw_updated_at` | TIMESTAMP | NN | |

---

## 6. Meter Reading

### `raw.meter_reading` (written by Dataflow streaming job)

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `reading_id` | STRING | NN | UUID generated by AMI simulator |
| `meter_id` | STRING | NN | FK → Meter |
| `reading_value` | FLOAT64 | NN | Must be >= 0 |
| `unit_of_measure` | STRING | NN | ENUM(kWh, m3, liters) |
| `reading_type` | STRING | NN | ENUM(INTERVAL, CUMULATIVE, MANUAL) |
| `read_at` | TIMESTAMP | NN | Device clock time; streaming watermark |
| `received_at` | TIMESTAMP | NN | Pub/Sub publish timestamp |
| `source_system` | STRING | NN | Identifier of the AMI publisher instance |
| `quality_flag` | STRING | NN | Set by Dataflow DQ check; ENUM(VALID, ESTIMATED, SUSPECT, REJECTED) |

**Partitioned by:** `DATE(read_at)`
**Clustered by:** `meter_id`

### `warehouse.fact_meter_reading`

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `reading_id` | STRING | NN PK | |
| `meter_sk` | INT64 | NN FK | Resolved from `dim_meter` at load time |
| `meter_id` | STRING | NN | Retained for convenience |
| `reading_value` | FLOAT64 | NN | |
| `unit_of_measure` | STRING | NN | |
| `reading_type` | STRING | NN | |
| `quality_flag` | STRING | NN | |
| `read_at` | TIMESTAMP | NN | |
| `received_at` | TIMESTAMP | NN | |
| `dw_inserted_at` | TIMESTAMP | NN | |

---

## 7. Bill

### `raw.bill` (written by Dataflow batch job from GCS Parquet files)

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `bill_id` | STRING | NN | UUID |
| `account_id` | STRING | NN | FK → Account |
| `contract_id` | STRING | NN | FK → Contract |
| `bill_date` | DATE | NN | Date bill was generated |
| `due_date` | DATE | NN | Payment deadline |
| `period_start` | DATE | NN | Billing period start |
| `period_end` | DATE | NN | Billing period end |
| `total_amount` | NUMERIC | NN | Must be > 0 |
| `currency` | STRING | NN | ISO 4217, e.g. USD |
| `bill_status` | STRING | NN | ENUM(ISSUED, PAID, OVERDUE, CANCELLED, DISPUTED) |
| `tax_amount` | NUMERIC | NN | Must be >= 0 |
| `usage_kwh` | FLOAT64 | YES | NULL for non-electricity bills |
| `created_at` | TIMESTAMP | NN | |
| `updated_at` | TIMESTAMP | NN | |

**Partitioned by:** `bill_date`
**Clustered by:** `account_id`

### `warehouse.fact_bill`

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `bill_id` | STRING | NN PK | |
| `customer_sk` | INT64 | NN FK | Resolved via account → customer join |
| `account_id` | STRING | NN | |
| `contract_id` | STRING | NN | |
| `bill_date` | DATE | NN | |
| `due_date` | DATE | NN | |
| `period_start` | DATE | NN | |
| `period_end` | DATE | NN | |
| `total_amount` | NUMERIC | NN | |
| `tax_amount` | NUMERIC | NN | |
| `usage_kwh` | FLOAT64 | YES | |
| `bill_status` | STRING | NN | |
| `dw_inserted_at` | TIMESTAMP | NN | |
| `dw_updated_at` | TIMESTAMP | NN | Updated when `bill_status` changes |

---

## 8. Payment

### `raw.payment` (written by Dataflow batch job from GCS CSV files)

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `payment_id` | STRING | NN | UUID |
| `bill_id` | STRING | NN | FK → Bill |
| `account_id` | STRING | NN | FK → Account (denormalized) |
| `amount` | NUMERIC | NN | Must be > 0 |
| `currency` | STRING | NN | ISO 4217 |
| `payment_method` | STRING | NN | ENUM(DIRECT_DEBIT, CREDIT_CARD, CHEQUE, BANK_TRANSFER) |
| `payment_status` | STRING | NN | ENUM(PENDING, CLEARED, REVERSED, FAILED) |
| `payment_date` | TIMESTAMP | NN | Customer-initiated time |
| `settled_at` | TIMESTAMP | YES | NULL until funds clear |
| `created_at` | TIMESTAMP | NN | |

**Partitioned by:** `DATE(payment_date)`
**Clustered by:** `account_id`

### `warehouse.fact_payment`

| Column | BQ Type | Nullable | Notes |
|--------|---------|----------|-------|
| `payment_id` | STRING | NN PK | |
| `bill_id` | STRING | NN FK | |
| `customer_sk` | INT64 | NN FK | Resolved at load time |
| `account_id` | STRING | NN | |
| `amount` | NUMERIC | NN | |
| `currency` | STRING | NN | |
| `payment_method` | STRING | NN | |
| `payment_status` | STRING | NN | |
| `payment_date` | TIMESTAMP | NN | |
| `settled_at` | TIMESTAMP | YES | |
| `dw_inserted_at` | TIMESTAMP | NN | |

---

## 9. Dead Letter Tables

### `dead_letter.quality_failures`

| Column | BQ Type | Notes |
|--------|---------|-------|
| `dlq_id` | STRING | UUID for this DLQ record |
| `source_pipeline` | STRING | Pipeline name (e.g., `billing_batch_ingest`) |
| `source_table` | STRING | Target table the row was destined for |
| `raw_payload` | JSON | Full row as JSON string |
| `error_code` | STRING | E.g., `NULL_REQUIRED`, `INVALID_ENUM`, `REF_INTEGRITY`, `SCHEMA_MISMATCH` |
| `error_message` | STRING | Human-readable description |
| `failed_at` | TIMESTAMP | When the failure was recorded |
| `retry_count` | INT64 | Number of reprocessing attempts |
| `last_retry_at` | TIMESTAMP | Time of last retry |
| `resolution_status` | STRING | ENUM(PENDING, REPROCESSED, ABANDONED) |

---

## 10. Quality Run Log

### `warehouse.dq_run_log`

| Column | BQ Type | Notes |
|--------|---------|-------|
| `run_id` | STRING | UUID for this DQ run |
| `batch_id` | STRING | Source batch/file identifier |
| `pipeline_name` | STRING | |
| `table_name` | STRING | Target table being validated |
| `rule_name` | STRING | Name of quality rule applied |
| `rows_checked` | INT64 | |
| `rows_passed` | INT64 | |
| `rows_failed` | INT64 | |
| `pass_rate` | FLOAT64 | rows_passed / rows_checked |
| `run_at` | TIMESTAMP | |
| `run_duration_seconds` | FLOAT64 | |

---

## 11. Mart Tables

### `marts.mart_revenue_monthly`

| Column | BQ Type | Notes |
|--------|---------|-------|
| `account_id` | STRING | |
| `month` | DATE | First day of the month |
| `total_billed` | NUMERIC | Sum of `fact_bill.total_amount` |
| `total_collected` | NUMERIC | Sum of `fact_payment.amount` WHERE status = CLEARED |
| `collection_rate` | FLOAT64 | total_collected / total_billed |
| `bill_count` | INT64 | |
| `payment_count` | INT64 | |

### `marts.mart_bill_payment_lag`

| Column | BQ Type | Notes |
|--------|---------|-------|
| `bill_id` | STRING | |
| `account_id` | STRING | |
| `bill_date` | DATE | |
| `due_date` | DATE | |
| `first_payment_date` | DATE | Earliest payment_date for this bill |
| `settled_date` | DATE | Earliest settled_at for this bill |
| `days_to_first_payment` | INT64 | first_payment_date - bill_date |
| `days_to_settlement` | INT64 | settled_date - bill_date; NULL if not yet settled |
| `is_overdue` | BOOL | payment_date > due_date |

### `marts.mart_unbilled_readings`

| Column | BQ Type | Notes |
|--------|---------|-------|
| `meter_id` | STRING | |
| `service_point_id` | STRING | |
| `read_date` | DATE | |
| `reading_count` | INT64 | Count of readings on that day |
| `total_kwh` | FLOAT64 | Sum of reading_value |
| `is_billed` | BOOL | TRUE if a bill exists covering this read_date |

### `marts.mart_pipeline_health`

| Column | BQ Type | Notes |
|--------|---------|-------|
| `pipeline_name` | STRING | |
| `run_date` | DATE | |
| `rows_read` | INT64 | |
| `rows_written` | INT64 | |
| `rows_dlq` | INT64 | |
| `dlq_rate` | FLOAT64 | rows_dlq / rows_read |
| `duration_seconds` | FLOAT64 | |
| `status` | STRING | ENUM(SUCCESS, PARTIAL, FAILED) |
