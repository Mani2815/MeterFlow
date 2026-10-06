-- Validation Query: Check for Duplicates in Core Facts and Dimensions
-- This query identifies if the MERGE strategy has failed to maintain uniqueness.

-- 1. Check dim_customer uniqueness
SELECT 
    customer_id, 
    COUNT(*) as record_count 
FROM `meter_to_cash_core.dim_customer`
GROUP BY customer_id
HAVING COUNT(*) > 1;

-- 2. Check fact_meter_reading uniqueness
SELECT 
    reading_id, 
    COUNT(*) as record_count 
FROM `meter_to_cash_core.fact_meter_reading`
GROUP BY reading_id
HAVING COUNT(*) > 1;

-- 3. Check fact_billing uniqueness
SELECT 
    bill_id, 
    COUNT(*) as record_count 
FROM `meter_to_cash_core.fact_billing`
GROUP BY bill_id
HAVING COUNT(*) > 1;
