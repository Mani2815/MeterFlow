/*
  queries.sql
  -----------
  Data Quality Validation & Example Reporting queries
*/

-- 1. Check for missing foreign keys in Facts (Orphans)
SELECT 
  'fact_billing' AS table_name,
  COUNT(*) AS orphan_records
FROM `meter_to_cash_core.fact_billing` fb
LEFT JOIN `meter_to_cash_core.dim_account` da ON fb.account_sk = da.account_sk
WHERE da.account_sk IS NULL;

-- 2. Check for duplicate natural keys in Dimensions
SELECT 
  customer_id, 
  COUNT(*) 
FROM `meter_to_cash_core.dim_customer`
GROUP BY customer_id 
HAVING COUNT(*) > 1;

-- 3. Monthly Revenue Mart Query (Example Aggregation)
SELECT 
  DATE_TRUNC(fb.bill_date, MONTH) AS billing_month,
  dc.customer_type,
  dco.commodity_type,
  SUM(fb.total_amount) AS total_revenue,
  COUNT(DISTINCT fb.bill_id) AS total_bills_issued
FROM `meter_to_cash_core.fact_billing` fb
JOIN `meter_to_cash_core.dim_account` da ON fb.account_sk = da.account_sk
JOIN `meter_to_cash_core.dim_customer` dc ON da.customer_sk = dc.customer_sk
JOIN `meter_to_cash_core.dim_contract` dco ON fb.contract_sk = dco.contract_sk
WHERE fb.bill_status != 'CANCELLED'
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 2, 3;
