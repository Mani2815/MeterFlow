# Phase 6: Data Quality and Error Management

## Production-style Data Quality Layer
This phase implements strict schema and business-rule validations to prevent corrupt or logically impossible data from silently polluting the analytical warehouse.

### 1. Python Validation Layer (`quality/validators.py`)
Intercepts data during Batch or Streaming loads (e.g. within Apache Beam or ingestion scripts) and checks for:
- **Required Fields**: Ensures primary keys exist.
- **Impossible Values**: Meter readings > 999,999.
- **Negative Quantities**: Rejects negative billing amounts and negative meter readings.
- **Invalid Timestamps**: Catches dummy dates like `0000-00-00`.

### 2. Error Routing (Dead Letter Queue & Quarantine)
- Invalid records are never silently dropped.
- **DLQ Model (`quality/dlq.py`)**: For streaming pipelines (CDC), rejected records are mapped to `DLQRecord` containing the raw `original_payload`, the specific `error_message`, the `processing_attempt_count`, and `source_system`.
- **Batch Quarantine (`quality/metrics.py`)**: For batch loads, metrics are aggregated (`BatchQualityMetrics`) recording how many were accepted vs rejected, and persisted to track historical pipeline health.

### 3. BigQuery Schemas (`warehouse/ddl/04_quality.sql`)
1. **`dead_letter_queue`**: Table storing DLQ events, partitioned by failure date. Allows data engineers to query unresolved errors, correct the payloads, and manually replay them.
2. **`batch_metrics`**: A run-level observability table logging execution times, rejection rates, and pipeline status.
3. **`vw_recon_meter_to_bill`**: A core business reconciliation view. It calculates `variance` by joining `fact_billing` -> `fact_consumption` -> `dim_contract` -> `dim_meter` -> `fact_meter_reading` to ensure what was billed matches the raw telemetry recorded in the warehouse for that period.
