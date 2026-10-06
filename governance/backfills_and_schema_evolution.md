# Historical Backfills and Schema Evolution

This document outlines the production-style design for handling historical data backfills and controlled schema evolution in the Utility Meter-to-Cash Cloud Data Platform.

## 1. Historical Backfills

Backfills are required when onboarding new utility accounts, recovering from severe data loss, or retroactively applying new business logic to historical data.

### Design Decisions & Capabilities
- **Configurability**: Backfills are triggered via `POST /api/v1/backfills`, requiring a specific `dataset` (source/table), `start_date`, and `end_date`.
- **Isolation**: Backfills receive an isolated `backfill_id` (e.g., `BF-20261006-XXXX`). This ID is injected into the Airflow DAG context and tagged on every BigQuery job. This allows us to track costs and monitor progress independently of normal ingestion.
- **Clear Distinction**: The `trigger_type` and `run_id` explicitly distinguish backfills from CDC streaming or daily scheduled batch runs. 
- **Idempotency & No Duplicates**: Backfills utilize the same idempotent `MERGE` logic (see `warehouse/dml/`) as standard batch processing. Running a backfill multiple times for the same date range will overwrite/update existing records based on the natural key, ensuring zero duplicate warehouse records.
- **Validation & Reconciliation**: Once a backfill completes, the orchestrator automatically triggers the Data Quality framework and the Meter-to-Bill reconciliation check (`quality/reconciliation/meter_to_bill.sql`) scoped specifically to the backfilled date range to ensure integrity.

## 2. Controlled Schema Evolution

As the utility platform grows, upstream systems (e.g., PostgreSQL billing app) will change their schemas. We must prevent silent data corruption in the warehouse.

### Design Decisions
- **Schema Registry / Versions**: All incoming streaming events and batch payloads are validated against a schema registry (or strict Pydantic/YAML definitions in `quality/rules/validation_rules.yaml`).
- **Backward-Compatible Changes**: 
  - *Adding a new nullable field*: Supported natively. The schema validation layer will accept the payload, and BigQuery will append the new column (via `SchemaUpdateOption.ALLOW_FIELD_ADDITION` on the load job). Old records simply receive `NULL` for the new field.
- **Incompatible Changes**:
  - *Data type changes (e.g., STRING to INT)* or *Dropping a required field*: These are strictly forbidden by the validation layer.
- **Failure Behavior**: If an incompatible payload is detected, it is immediately routed to the Dead Letter Queue (`meter_to_cash_quality.dead_letter_queue`) with `error_category = 'SCHEMA_MISMATCH'`. The pipeline *will not crash*, but the DLQ metrics will spike, alerting the data engineering team.
- **Event Recording**: Any accepted schema evolution (e.g., adding a field) generates an audit event logged in our operational Postgres DB (`schema_version` table, to be implemented if not already).

## 3. Test Scenarios (See `tests/test_schema_and_backfill.py`)

We have defined robust test scenarios to prove these capabilities:
1. **Add a new nullable field**: Proves that adding `discount_code` to a billing event doesn't break ingestion.
2. **Process old records**: Proves that records lacking the new field are safely ingested as `NULL`.
3. **Process new records**: Proves that records with the new field populate correctly.
4. **Perform a historical backfill**: Triggers a backfill over a 6-month period, ensuring data lands properly.
5. **Rerun the same backfill**: Proves idempotency; record counts remain identical after a second run.
6. **Simulate an incompatible type change**: Proves that changing `amount` from `FLOAT` to `STRING` fails validation and routes to the DLQ instead of corrupting BigQuery.
