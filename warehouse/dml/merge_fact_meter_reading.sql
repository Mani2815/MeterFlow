-- MERGE Script for fact_meter_reading
-- Handles incremental load, deduplication, and late-arriving records.
-- Late arriving records are handled gracefully because BigQuery routes them to the correct partition based on reading_timestamp.

MERGE `meter_to_cash_core.fact_meter_reading` T
USING (
    SELECT 
        CAST(FARM_FINGERPRINT(reading_id) AS STRING) as reading_sk,
        CAST(FARM_FINGERPRINT(meter_id) AS STRING) as meter_sk,
        CAST(FORMAT_TIMESTAMP('%Y%m%d', reading_timestamp) AS INT64) as date_sk,
        reading_id,
        reading_value,
        unit,
        reading_timestamp,
        'datastream_events' as source_system
    FROM (
        SELECT 
            *,
            -- Deduplicate by reading_id, picking the most recently ingested event
            ROW_NUMBER() OVER (PARTITION BY reading_id ORDER BY reading_timestamp DESC) as rn
        FROM `meter_to_cash_staging.stg_readings`
        -- In production, filter for only newly arrived rows using a high-water mark or execution date
        -- WHERE ingestion_timestamp >= @last_run_timestamp
    )
    WHERE rn = 1
) S
ON T.reading_id = S.reading_id
    -- Partition pruning filter for the merge operation (assuming a 3-day late-arrival window for optimal performance)
    -- AND T.reading_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 DAY)
WHEN MATCHED AND T.reading_value != S.reading_value THEN
    UPDATE SET 
        reading_value = S.reading_value,
        unit = S.unit,
        dw_created_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (
        reading_sk,
        meter_sk,
        date_sk,
        reading_id,
        reading_value,
        unit,
        reading_timestamp,
        source_system,
        dw_created_at
    )
    VALUES (
        S.reading_sk,
        S.meter_sk,
        S.date_sk,
        S.reading_id,
        S.reading_value,
        S.unit,
        S.reading_timestamp,
        S.source_system,
        CURRENT_TIMESTAMP()
    );
