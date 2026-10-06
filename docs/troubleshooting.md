# Troubleshooting Guide

Use this guide when diagnosing failures in the Meter-to-Cash Data Platform.

## 1. Pipeline Run Failed in Airflow
**Symptoms**: Airflow DAG `meter_to_cash_daily_batch` shows a red status.
**Action**:
1. Check Airflow task logs for the exact point of failure.
2. If `load_to_staging` failed: Check if the source database credentials rotated or if there are network connectivity issues.
3. If `run_quality_checks` failed: A critical quality threshold was breached. Review `meter_to_cash_quality.data_quality_metrics` in BigQuery to identify which dataset caused the halt.

## 2. Unexplained Drop in Processed Records
**Symptoms**: Overview Dashboard shows a 30% drop in records processed. No explicit DAG failures.
**Action**:
1. **Check the DLQ**: Did validation rules change? If the DLQ count spiked simultaneously, payloads are being rejected before loading. Review the `error_message` in the DLQ table.
2. **Check Source System CDC**: Verify that GCP Datastream/Pub-Sub is actively publishing events and hasn't stalled.

## 3. High Volume of DLQ Events: "SCHEMA_MISMATCH"
**Symptoms**: Streaming pipeline routes thousands of messages to the DLQ.
**Action**:
1. Inspect the `original_payload` column in the DLQ table.
2. Compare the payload structure to `quality/rules/validation_rules.yaml`.
3. If the upstream system intentionally rolled out a new schema, update the YAML rules to accept the new format (if backward compatible) and execute an API Replay (`POST /api/v1/dlq/{id}/replay`).

## 4. Reconciliation Mismatch Flagged
**Symptoms**: The `meter_to_bill.sql` query output shows `ZERO_BILL_WITH_CONSUMPTION`.
**Action**:
1. Isolate the affected `account_sk`.
2. Query `fact_consumption` to confirm the physical meter registered usage.
3. Query `fact_payment` and `fact_billing` to see if a payment was applied to a different bill, or if the billing engine failed to generate an invoice for that specific month. Elevate to the core Billing Engineering team.
