/*
  03_facts.sql
  ------------
  Creates the Core Fact tables with strict partitioning and clustering.
*/

CREATE TABLE IF NOT EXISTS meter_to_cash_core.fact_meter_reading (
  reading_sk INT64 NOT NULL,
  reading_id STRING NOT NULL,
  meter_sk INT64 NOT NULL,
  
  reading_value NUMERIC,
  unit_of_measure STRING,
  reading_type STRING,
  quality_flag STRING,
  
  read_at TIMESTAMP NOT NULL,
  
  -- Audit
  source_system STRING,
  bq_insert_timestamp TIMESTAMP
)
PARTITION BY DATE(read_at)
CLUSTER BY (meter_sk, quality_flag);


CREATE TABLE IF NOT EXISTS meter_to_cash_core.fact_billing (
  bill_sk INT64 NOT NULL,
  bill_id STRING NOT NULL,
  account_sk INT64 NOT NULL,
  contract_sk INT64 NOT NULL,
  
  bill_date DATE NOT NULL,
  due_date DATE,
  total_amount NUMERIC,
  tax_amount NUMERIC,
  bill_status STRING,
  
  -- Audit
  source_system STRING,
  bq_insert_timestamp TIMESTAMP,
  bq_update_timestamp TIMESTAMP
)
PARTITION BY DATE_TRUNC(bill_date, MONTH)
CLUSTER BY (account_sk, contract_sk, bill_status);


CREATE TABLE IF NOT EXISTS meter_to_cash_core.fact_payment (
  payment_sk INT64 NOT NULL,
  payment_id STRING NOT NULL,
  bill_sk INT64 NOT NULL,
  account_sk INT64 NOT NULL,
  
  payment_date TIMESTAMP NOT NULL,
  amount NUMERIC,
  payment_method STRING,
  payment_status STRING,
  
  -- Audit
  source_system STRING,
  bq_insert_timestamp TIMESTAMP,
  bq_update_timestamp TIMESTAMP
)
PARTITION BY DATE_TRUNC(DATE(payment_date), MONTH)
CLUSTER BY (account_sk, bill_sk, payment_status);


CREATE TABLE IF NOT EXISTS meter_to_cash_core.fact_consumption (
  consumption_sk INT64 NOT NULL,
  bill_sk INT64 NOT NULL,
  contract_sk INT64 NOT NULL,
  
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  
  usage_amount NUMERIC,
  usage_unit STRING,
  
  -- Audit
  source_system STRING,
  bq_insert_timestamp TIMESTAMP,
  bq_update_timestamp TIMESTAMP
)
PARTITION BY DATE_TRUNC(period_start, MONTH)
CLUSTER BY (contract_sk, bill_sk);
