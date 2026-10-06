-- MERGE Script for dim_customer (SCD Type 1)
-- Handles deduplication from the staging layer by picking the latest record (source_updated_at)
-- Uses FARM_FINGERPRINT for surrogate key generation

MERGE `meter_to_cash_core.dim_customer` T
USING (
    SELECT 
        CAST(FARM_FINGERPRINT(customer_id) AS STRING) as customer_sk,
        customer_id,
        first_name,
        last_name,
        email,
        phone,
        'postgres_ops' as source_system,
        source_updated_at
    FROM (
        SELECT 
            *,
            ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY source_updated_at DESC) as rn
        FROM `meter_to_cash_staging.stg_customers`
        -- Optional: WHERE source_updated_at > (SELECT MAX(dw_updated_at) FROM `meter_to_cash_core.dim_customer`)
    )
    WHERE rn = 1
) S
ON T.customer_id = S.customer_id
WHEN MATCHED AND T.dw_updated_at < S.source_updated_at THEN
    UPDATE SET 
        first_name = S.first_name,
        last_name = S.last_name,
        email = S.email,
        phone = S.phone,
        dw_updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (
        customer_sk, 
        customer_id, 
        first_name, 
        last_name, 
        email, 
        phone, 
        source_system, 
        dw_created_at, 
        dw_updated_at
    )
    VALUES (
        S.customer_sk, 
        S.customer_id, 
        S.first_name, 
        S.last_name, 
        S.email, 
        S.phone, 
        S.source_system, 
        CURRENT_TIMESTAMP(), 
        CURRENT_TIMESTAMP()
    );
