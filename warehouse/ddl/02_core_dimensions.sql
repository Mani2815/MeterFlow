-- Core Dimensions

CREATE TABLE IF NOT EXISTS `meter_to_cash_core.dim_customer` (
    customer_sk STRING NOT NULL,
    customer_id STRING NOT NULL,
    first_name STRING,
    last_name STRING,
    email STRING,
    phone STRING,
    source_system STRING NOT NULL,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY customer_id;

CREATE TABLE IF NOT EXISTS `meter_to_cash_core.dim_account` (
    account_sk STRING NOT NULL,
    account_id STRING NOT NULL,
    customer_sk STRING NOT NULL,
    status STRING,
    billing_address STRING,
    source_system STRING NOT NULL,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY status, customer_sk;

CREATE TABLE IF NOT EXISTS `meter_to_cash_core.dim_meter` (
    meter_sk STRING NOT NULL,
    meter_id STRING NOT NULL,
    serial_number STRING,
    model STRING,
    installation_date DATE,
    status STRING,
    service_point_sk STRING,
    source_system STRING NOT NULL,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY status, model;

CREATE TABLE IF NOT EXISTS `meter_to_cash_core.dim_service_point` (
    service_point_sk STRING NOT NULL,
    service_point_id STRING NOT NULL,
    location_sk STRING,
    premise_type STRING,
    status STRING,
    source_system STRING NOT NULL,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY premise_type, status;

CREATE TABLE IF NOT EXISTS `meter_to_cash_core.dim_location` (
    location_sk STRING NOT NULL,
    postal_code STRING,
    city STRING,
    state STRING,
    country STRING,
    source_system STRING NOT NULL,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY state, city;

CREATE TABLE IF NOT EXISTS `meter_to_cash_core.dim_date` (
    date_sk INT64 NOT NULL,
    full_date DATE NOT NULL,
    year INT64,
    month INT64,
    day INT64,
    quarter INT64,
    day_of_week INT64,
    is_weekend BOOLEAN
)
CLUSTER BY year, month;
