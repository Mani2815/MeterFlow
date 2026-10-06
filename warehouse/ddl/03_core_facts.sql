-- Core Facts

CREATE TABLE IF NOT EXISTS `meter_to_cash_core.fact_meter_reading` (
    reading_sk STRING NOT NULL,
    meter_sk STRING NOT NULL,
    date_sk INT64 NOT NULL,
    reading_id STRING NOT NULL,
    reading_value FLOAT64 NOT NULL,
    unit STRING,
    reading_timestamp TIMESTAMP NOT NULL,
    source_system STRING NOT NULL,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(reading_timestamp)
CLUSTER BY meter_sk;


CREATE TABLE IF NOT EXISTS `meter_to_cash_core.fact_billing` (
    bill_sk STRING NOT NULL,
    account_sk STRING NOT NULL,
    date_sk INT64 NOT NULL,
    bill_id STRING NOT NULL,
    total_amount FLOAT64 NOT NULL,
    currency STRING,
    issue_date TIMESTAMP NOT NULL,
    due_date TIMESTAMP,
    status STRING,
    source_system STRING NOT NULL,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(issue_date)
CLUSTER BY account_sk, status;


CREATE TABLE IF NOT EXISTS `meter_to_cash_core.fact_payment` (
    payment_sk STRING NOT NULL,
    account_sk STRING NOT NULL,
    bill_sk STRING,
    date_sk INT64 NOT NULL,
    payment_id STRING NOT NULL,
    amount FLOAT64 NOT NULL,
    currency STRING,
    payment_method STRING,
    payment_timestamp TIMESTAMP NOT NULL,
    status STRING,
    source_system STRING NOT NULL,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(payment_timestamp)
CLUSTER BY account_sk, payment_method;


CREATE TABLE IF NOT EXISTS `meter_to_cash_core.fact_consumption` (
    consumption_sk STRING NOT NULL,
    meter_sk STRING NOT NULL,
    account_sk STRING NOT NULL,
    date_sk INT64 NOT NULL,
    consumption_date DATE NOT NULL,
    total_consumption FLOAT64 NOT NULL,
    unit STRING,
    reading_count INT64,
    source_system STRING NOT NULL,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY consumption_date
CLUSTER BY meter_sk, account_sk;
