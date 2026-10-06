-- Staging Views / External Tables (Conceptual)
-- In a real environment, these point to raw ingested data in BigQuery

CREATE OR REPLACE VIEW `meter_to_cash_staging.stg_customers` AS
SELECT 
    id as customer_id,
    first_name,
    last_name,
    email,
    phone,
    created_at as source_created_at,
    updated_at as source_updated_at
FROM `meter_raw_dev.customers`;

CREATE OR REPLACE VIEW `meter_to_cash_staging.stg_accounts` AS
SELECT 
    id as account_id,
    customer_id,
    status,
    billing_address,
    created_at as source_created_at,
    updated_at as source_updated_at
FROM `meter_raw_dev.accounts`;

CREATE OR REPLACE VIEW `meter_to_cash_staging.stg_meters` AS
SELECT 
    id as meter_id,
    serial_number,
    model,
    installation_date,
    status,
    service_point_id
FROM `meter_raw_dev.meters`;

CREATE OR REPLACE VIEW `meter_to_cash_staging.stg_readings` AS
SELECT 
    id as reading_id,
    meter_id,
    reading_value,
    unit,
    reading_timestamp
FROM `meter_raw_dev.readings`;
