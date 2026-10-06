-- Meter-to-Bill Reconciliation Check
-- Goal: Ensure that the consumption we billed for matches the physical consumption recorded by the meters.

WITH monthly_consumption AS (
    -- Aggregate physical meter consumption by account and month
    SELECT 
        c.account_sk,
        d.year,
        d.month,
        SUM(c.total_consumption) as expected_physical_consumption
    FROM `meter_to_cash_core.fact_consumption` c
    JOIN `meter_to_cash_core.dim_date` d ON c.date_sk = d.date_sk
    GROUP BY c.account_sk, d.year, d.month
),

monthly_billing AS (
    -- Aggregate billed amounts (and potentially billed consumption if tracked in billing lines) by account and month
    SELECT 
        b.account_sk,
        d.year,
        d.month,
        -- In a real utility, fact_billing or fact_billing_line_item would store the 'billed_consumption' amount.
        -- Assuming we have a standard rate applied to the bill total_amount to derive billed consumption for this example:
        SUM(b.total_amount) as total_billed_amount,
        COUNT(b.bill_sk) as bill_count
    FROM `meter_to_cash_core.fact_billing` b
    JOIN `meter_to_cash_core.dim_date` d ON b.date_sk = d.date_sk
    WHERE b.status = 'ISSUED' OR b.status = 'PAID'
    GROUP BY b.account_sk, d.year, d.month
)

SELECT 
    mc.account_sk,
    mc.year,
    mc.month,
    mc.expected_physical_consumption,
    mb.total_billed_amount,
    mb.bill_count,
    -- Reconciliation Flags
    CASE 
        WHEN mb.account_sk IS NULL THEN 'NO_BILL_ISSUED'
        WHEN mb.total_billed_amount <= 0 AND mc.expected_physical_consumption > 0 THEN 'ZERO_BILL_WITH_CONSUMPTION'
        ELSE 'OK'
    END as reconciliation_status
FROM monthly_consumption mc
LEFT JOIN monthly_billing mb 
    ON mc.account_sk = mb.account_sk 
    AND mc.year = mb.year 
    AND mc.month = mb.month
WHERE 
    mb.account_sk IS NULL -- Unbilled consumption
    OR (mb.total_billed_amount <= 0 AND mc.expected_physical_consumption > 0)
ORDER BY mc.year DESC, mc.month DESC, mc.expected_physical_consumption DESC;
