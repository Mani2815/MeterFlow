/*
  merge_facts.sql
  ---------------
  Idempotent logic for Facts. 
  For append-only telemetry (readings), we use a deduplicating INSERT.
  For mutating events (bills, payments), we use MERGE.
*/

-- 1. fact_meter_reading (Append Only, Deduplicated)
-- In a real scenario, this runs incrementally using a high-watermark on read_at.
INSERT INTO `meter_to_cash_core.fact_meter_reading` (
  reading_sk, reading_id, meter_sk, reading_value, unit_of_measure, 
  reading_type, quality_flag, read_at, source_system, bq_insert_timestamp
)
SELECT 
  FARM_FINGERPRINT(reading_id) AS reading_sk,
  reading_id,
  FARM_FINGERPRINT(meter_id) AS meter_sk,
  CAST(JSON_EXTRACT_SCALAR(payload, '$.reading_value') AS NUMERIC),
  JSON_EXTRACT_SCALAR(payload, '$.unit_of_measure'),
  JSON_EXTRACT_SCALAR(payload, '$.reading_type'),
  JSON_EXTRACT_SCALAR(payload, '$.quality_flag'),
  CAST(JSON_EXTRACT_SCALAR(payload, '$.read_at') AS TIMESTAMP),
  source_system,
  CURRENT_TIMESTAMP()
FROM `meter_to_cash_stg.stg_meter_readings` S
WHERE NOT EXISTS (
  SELECT 1 FROM `meter_to_cash_core.fact_meter_reading` T
  WHERE T.reading_id = JSON_EXTRACT_SCALAR(S.payload, '$.reading_id')
);


-- 2. fact_billing (UPSERT)
MERGE `meter_to_cash_core.fact_billing` T
USING (
  SELECT 
    FARM_FINGERPRINT(bill_id) AS bill_sk,
    bill_id,
    FARM_FINGERPRINT(account_id) AS account_sk,
    FARM_FINGERPRINT(contract_id) AS contract_sk,
    bill_date,
    due_date,
    total_amount,
    tax_amount,
    bill_status,
    source_system,
    event_timestamp
  FROM `meter_to_cash_stg.stg_bills`
  WHERE operation IN ('INSERT', 'UPDATE')
) S
ON T.bill_id = S.bill_id
WHEN MATCHED AND S.event_timestamp >= T.bq_update_timestamp THEN
  UPDATE SET
    bill_date = S.bill_date,
    due_date = S.due_date,
    total_amount = S.total_amount,
    tax_amount = S.tax_amount,
    bill_status = S.bill_status,
    bq_update_timestamp = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
  INSERT (
    bill_sk, bill_id, account_sk, contract_sk, bill_date, due_date,
    total_amount, tax_amount, bill_status, source_system, bq_insert_timestamp, bq_update_timestamp
  )
  VALUES (
    S.bill_sk, S.bill_id, S.account_sk, S.contract_sk, S.bill_date, S.due_date,
    S.total_amount, S.tax_amount, S.bill_status, S.source_system, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
  );
