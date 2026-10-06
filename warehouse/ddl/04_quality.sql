CREATE SCHEMA IF NOT EXISTS meter_to_cash_quality;

CREATE TABLE IF NOT EXISTS meter_to_cash_quality.dead_letter_queue (
    dlq_id STRING NOT NULL,
    source_system STRING NOT NULL,
    source_table STRING NOT NULL,
    original_payload STRING NOT NULL,
    error_category STRING NOT NULL,
    error_message STRING NOT NULL,
    processing_attempt_count INT64 NOT NULL,
    failure_timestamp TIMESTAMP NOT NULL,
    status STRING DEFAULT 'UNRESOLVED'
)
PARTITION BY DATE(failure_timestamp);

CREATE TABLE IF NOT EXISTS meter_to_cash_quality.batch_metrics (
    run_id STRING NOT NULL,
    pipeline_name STRING NOT NULL,
    source STRING NOT NULL,
    records_received INT64,
    records_processed INT64,
    records_rejected INT64,
    duplicate_count INT64,
    null_count INT64,
    validation_failures INT64,
    execution_time_seconds INT64,
    status STRING,
    run_timestamp TIMESTAMP NOT NULL
)
PARTITION BY DATE(run_timestamp);

-- Reconciliation: Expected Meter Read vs Billed Consumption
CREATE OR REPLACE VIEW meter_to_cash_quality.vw_recon_meter_to_bill AS
SELECT 
    fb.bill_id,
    fb.contract_sk,
    fc.usage_amount AS billed_consumption,
    SUM(fmr.reading_value) AS expected_consumption,
    (fc.usage_amount - SUM(fmr.reading_value)) AS variance
FROM `meter_to_cash_core.fact_billing` fb
JOIN `meter_to_cash_core.fact_consumption` fc ON fb.bill_sk = fc.bill_sk
JOIN `meter_to_cash_core.dim_contract` dc ON fb.contract_sk = dc.contract_sk
JOIN `meter_to_cash_core.dim_meter` dm ON dm.service_point_sk = dc.location_sk
JOIN `meter_to_cash_core.fact_meter_reading` fmr ON dm.meter_sk = fmr.meter_sk 
    AND fmr.read_at BETWEEN fc.period_start AND fc.period_end
GROUP BY 1, 2, 3;
