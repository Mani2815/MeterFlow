/*
  02_dimensions.sql
  -----------------
  Creates the Core Dimension tables.
*/

CREATE SCHEMA IF NOT EXISTS meter_to_cash_core;

CREATE TABLE IF NOT EXISTS meter_to_cash_core.dim_customer (
  customer_sk INT64 NOT NULL,
  customer_id STRING NOT NULL,
  customer_number STRING NOT NULL,
  first_name STRING,
  last_name STRING,
  email STRING,
  customer_type STRING,
  status STRING,
  
  -- Audit
  source_system STRING,
  bq_insert_timestamp TIMESTAMP,
  bq_update_timestamp TIMESTAMP
)
CLUSTER BY (customer_sk, customer_id);

CREATE TABLE IF NOT EXISTS meter_to_cash_core.dim_account (
  account_sk INT64 NOT NULL,
  account_id STRING NOT NULL,
  account_number STRING NOT NULL,
  customer_sk INT64 NOT NULL,
  account_status STRING,
  billing_cycle STRING,
  
  -- Audit
  source_system STRING,
  bq_insert_timestamp TIMESTAMP,
  bq_update_timestamp TIMESTAMP
)
CLUSTER BY (account_sk, customer_sk);

CREATE TABLE IF NOT EXISTS meter_to_cash_core.dim_location (
  location_sk INT64 NOT NULL,
  premise_id STRING NOT NULL,
  premise_number STRING NOT NULL,
  address_line_1 STRING,
  city STRING,
  state STRING,
  postal_code STRING,
  grid_zone STRING,
  
  -- Audit
  source_system STRING,
  bq_insert_timestamp TIMESTAMP,
  bq_update_timestamp TIMESTAMP
)
CLUSTER BY (location_sk, premise_id);

CREATE TABLE IF NOT EXISTS meter_to_cash_core.dim_contract (
  contract_sk INT64 NOT NULL,
  contract_id STRING NOT NULL,
  contract_number STRING NOT NULL,
  account_sk INT64 NOT NULL,
  location_sk INT64 NOT NULL,
  commodity_type STRING,
  tariff_code STRING,
  status STRING,
  
  -- Audit
  source_system STRING,
  bq_insert_timestamp TIMESTAMP,
  bq_update_timestamp TIMESTAMP
)
CLUSTER BY (contract_sk, account_sk);

CREATE TABLE IF NOT EXISTS meter_to_cash_core.dim_meter (
  meter_sk INT64 NOT NULL,
  meter_id STRING NOT NULL,
  meter_serial_number STRING NOT NULL,
  service_point_sk INT64 NOT NULL,
  meter_type STRING,
  commodity_type STRING,
  status STRING,
  installation_date DATE,
  decommission_date DATE,
  
  -- Audit
  source_system STRING,
  bq_insert_timestamp TIMESTAMP,
  bq_update_timestamp TIMESTAMP
)
CLUSTER BY (meter_sk, meter_serial_number);
