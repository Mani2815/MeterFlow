# End-to-End Test Plan

This testing methodology ensures the absolute correctness of the Meter-to-Cash data platform across streaming, batch, and quality workflows.

## 1. Core Loading Capabilities
1. **Initial Load**: Validate that bulk ingestion of 10M+ records correctly populates dimensions and facts without timeouts.
2. **Incremental Load**: Trigger a daily batch run. Assert that only new/modified records since the high-water mark are extracted and loaded.

## 2. Change Data Capture (CDC) Streams
3. **CDC INSERT**: Insert a new reading into the source DB. Verify it appears in BigQuery `fact_meter_reading` within SLA (e.g., < 3 mins).
4. **CDC UPDATE**: Update a customer's `billing_address`. Verify `dim_account` updates successfully via SCD Type 1 MERGE.
5. **CDC DELETE**: Delete a record at the source. Verify the warehouse handles soft-deletes (e.g. marking `status = 'INACTIVE'`) rather than hard-deleting facts.

## 3. Streaming Event Handling
6. **Valid Dataflow Event**: Push a syntactically correct JSON payload to Pub/Sub. Ensure Dataflow parses, validates, and streams it into BigQuery.
7. **Invalid Event**: Push a malformed JSON or schema-violating payload (e.g., negative payment amount).
8. **DLQ Routing**: Confirm the invalid event (from #7) is entirely absent from BigQuery Core, but present in the Dead Letter Queue with the original payload intact.
9. **DLQ Replay**: Fix the validation rule (or payload), trigger the API Replay endpoint, and assert the record successfully merges into BigQuery.

## 4. Backfills & Evolution
10. **Backfill Execution**: Run a backfill for a 3-month window. Assert that records are accurately loaded.
11. **Backfill Rerun (Idempotency)**: Rerun the exact same backfill from #10. Assert that `duplicate_count` is 0 and total table rows remain exactly the same.
12. **Schema Evolution**: Introduce a new nullable column to the source. Verify pipeline dynamically accommodates the new field without halting.

## 5. Resilience & Quality
13. **Reconciliation Mismatch**: Artificially delete a billed amount in BigQuery. Verify the `meter_to_bill.sql` query catches the discrepancy and flags `ZERO_BILL_WITH_CONSUMPTION`.
14. **Pipeline Failure & Retry**: Manually kill the Airflow 'validate' task mid-flight. Verify Airflow retries automatically, and the pipeline resumes without data corruption.
