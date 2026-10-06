/*
  merge_dimensions.sql
  --------------------
  Idempotent UPSERT logic for Dimensions.
  To be scheduled via Airflow/Cloud Composer or BQ Scheduled Queries.
*/

-- MERGE dim_customer
MERGE `meter_to_cash_core.dim_customer` T
USING (
  SELECT 
    FARM_FINGERPRINT(customer_id) AS customer_sk,
    customer_id,
    customer_number,
    first_name,
    last_name,
    email,
    customer_type,
    status,
    source_system,
    event_timestamp
  FROM `meter_to_cash_stg.stg_customers`
  WHERE operation IN ('INSERT', 'UPDATE')
) S
ON T.customer_id = S.customer_id
WHEN MATCHED AND S.event_timestamp >= T.bq_update_timestamp THEN
  UPDATE SET
    customer_number = S.customer_number,
    first_name = S.first_name,
    last_name = S.last_name,
    email = S.email,
    customer_type = S.customer_type,
    status = S.status,
    source_system = S.source_system,
    bq_update_timestamp = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
  INSERT (
    customer_sk, customer_id, customer_number, first_name, last_name, email, 
    customer_type, status, source_system, bq_insert_timestamp, bq_update_timestamp
  )
  VALUES (
    S.customer_sk, S.customer_id, S.customer_number, S.first_name, S.last_name, S.email, 
    S.customer_type, S.status, S.source_system, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
  );

-- (Similar MERGE statements would follow for dim_account, dim_contract, dim_meter, etc.)
