-- Data Quality Metrics Table
-- Stores the results of data quality checks at the batch/run level

CREATE TABLE IF NOT EXISTS `meter_to_cash_quality.data_quality_metrics` (
    run_id STRING NOT NULL,
    pipeline_name STRING NOT NULL,
    source STRING NOT NULL,
    dataset STRING NOT NULL,
    records_received INT64 NOT NULL,
    records_processed INT64 NOT NULL,
    records_rejected INT64 NOT NULL,
    duplicate_count INT64 DEFAULT 0,
    null_count INT64 DEFAULT 0,
    validation_failures INT64 DEFAULT 0,
    execution_time_ms INT64,
    status STRING NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY pipeline_name, status;

-- Dead Letter Queue (DLQ) Table
-- Stores malformed streaming and batch records that failed validation

CREATE TABLE IF NOT EXISTS `meter_to_cash_quality.dead_letter_queue` (
    event_id STRING NOT NULL,
    run_id STRING,
    pipeline_name STRING NOT NULL,
    source STRING NOT NULL,
    dataset STRING NOT NULL,
    error_category STRING NOT NULL, -- e.g., 'SCHEMA_MISMATCH', 'VALIDATION_FAILED'
    error_message STRING NOT NULL,
    failed_field STRING,
    original_payload STRING NOT NULL, -- Full JSON payload preserved
    attempt_count INT64 DEFAULT 1,
    failure_timestamp TIMESTAMP NOT NULL,
    status STRING DEFAULT 'PENDING', -- PENDING, REPLAYED, RESOLVED, IGNORED
    resolved_at TIMESTAMP
)
PARTITION BY DATE(failure_timestamp)
CLUSTER BY status, dataset;

-- Quarantine Table
-- Used for batch processing specifically, where entire files or batches are temporarily stored

CREATE TABLE IF NOT EXISTS `meter_to_cash_quality.quarantine_records` (
    quarantine_id STRING NOT NULL,
    run_id STRING NOT NULL,
    dataset STRING NOT NULL,
    original_file_uri STRING,
    record_content STRING NOT NULL,
    rejection_reason STRING NOT NULL,
    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(quarantined_at)
CLUSTER BY dataset;
