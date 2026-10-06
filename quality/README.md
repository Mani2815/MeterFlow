# Data Quality & Error Management Layer

This module defines the production-style error handling, data quality checking, and reconciliation processes for the Utility Meter-to-Cash Data Platform.

## 1. Validation Rules (`rules/validation_rules.yaml`)
We use a declarative YAML structure to define rules for each dataset (`meter_readings`, `payments`, `bills`).
Validations include:
- **Required fields** (e.g., `meter_id`, `amount`)
- **Schema/Type validity**
- **Thresholds/Bounds** (e.g., negative quantities not allowed, impossible meter readings > 10000)
- **Timestamps** (e.g., no future dates)
- **Business Rule violations**
- **Referential Integrity** (e.g., invalid foreign-key relationships)

## 2. Failure Handling Strategies

### Streaming Failures (via Dataflow / Datastream -> Pub/Sub)
- **DLQ Routing**: Any message failing validation is immediately routed to the Dead Letter Queue (DLQ).
- **Error Metadata**: The DLQ preserves the original JSON payload along with rich context: failure timestamp, source table, attempt count, categorization (e.g. `SCHEMA_MISMATCH`), and the specific error message.
- **Replayability**: The `event_id` is tracked. The Control Plane API supports controlled replay of these payloads once upstream issues are resolved (e.g. `POST /api/v1/dlq/{event_id}/replay`).

### Batch Failures (via Airflow / DBT)
- **Quarantine**: During batch ETL, records violating rules are split from the main pipeline and written to a quarantine location (`meter_to_cash_quality.quarantine_records`).
- **Batch Metrics**: The entire batch run maintains metrics (records received, processed, rejected). If the rejection percentage exceeds a safety threshold (e.g., 5%), the entire batch fails and halts downstream processing.

## 3. BigQuery Quality Tables (`ddl/quality_tables.sql`)
1. **`data_quality_metrics`**: Tracks `run_id`, `pipeline_name`, `records_received`, `records_processed`, `records_rejected`, `duplicate_count`, `validation_failures`, etc.
2. **`dead_letter_queue`**: Stores streaming DLQ payloads with full context and replay status.
3. **`quarantine_records`**: Stores rejected batch records for inspection.

## 4. Reconciliation (`reconciliation/meter_to_bill.sql`)
Reconciliation queries ensure systemic integrity across the platform boundaries. 
For example, the `meter_to_bill` check joins physical `fact_consumption` against financial `fact_billing` grouped by `account_sk` and `month`. It flags:
- Accounts with recorded consumption but no corresponding bill (`NO_BILL_ISSUED`).
- Accounts with zero-dollar bills despite having positive physical consumption (`ZERO_BILL_WITH_CONSUMPTION`).
These anomalies are surfaced to the `operations/monitoring` dashboard.
