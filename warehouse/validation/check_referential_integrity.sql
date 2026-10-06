-- Validation Query: Check Referential Integrity
-- Because BigQuery does not enforce foreign keys physically, we must validate logically.

-- 1. Check for orphaned accounts (Account exists without a Customer)
SELECT a.account_id, a.customer_sk
FROM `meter_to_cash_core.dim_account` a
LEFT JOIN `meter_to_cash_core.dim_customer` c 
  ON a.customer_sk = c.customer_sk
WHERE c.customer_sk IS NULL;

-- 2. Check for orphaned meter readings (Reading exists without a valid Meter)
SELECT r.reading_id, r.meter_sk
FROM `meter_to_cash_core.fact_meter_reading` r
LEFT JOIN `meter_to_cash_core.dim_meter` m 
  ON r.meter_sk = m.meter_sk
WHERE m.meter_sk IS NULL;

-- 3. Check for orphaned bills (Bill exists without a valid Account)
SELECT b.bill_id, b.account_sk
FROM `meter_to_cash_core.fact_billing` b
LEFT JOIN `meter_to_cash_core.dim_account` a 
  ON b.account_sk = a.account_sk
WHERE a.account_sk IS NULL;
