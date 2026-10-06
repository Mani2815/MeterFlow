# Platform Observability & Monitoring

The Utility Meter-to-Cash Data Platform requires rigorous observability to ensure that data lands reliably, correctly, and on time. We monitor these key dimensions using Datadog/Cloud Monitoring wired into our backend FastAPI metrics endpoint.

## 1. Pipeline Latency
- **Metric**: `pipeline.duration.milliseconds`
- **Definition**: The total time taken from the start of extraction to the completion of reconciliation.
- **Alerting Threshold**: > 2 hours for the daily batch. > 5 minutes for streaming ingestion delays (Lag).
- **Dashboard Usage**: Used to detect slow database queries, API throttling, or Airflow scheduling bottlenecks.

## 2. Records Processed
- **Metric**: `pipeline.records.processed`
- **Definition**: The volume of valid records successfully written to the BigQuery Core layer.
- **Alerting Threshold**: If volume drops > 20% compared to the 7-day trailing average (indicating upstream failure or extraction bug).

## 3. Pipeline Failures
- **Metric**: `pipeline.runs.failed`
- **Definition**: A boolean/counter metric tracking uncaught exceptions or DAG failures.
- **Alerting Threshold**: > 0 (Immediate PagerDuty alert). 

## 4. DLQ Volume
- **Metric**: `dlq.events.received`
- **Definition**: The number of streaming records routed to the Dead Letter Queue.
- **Alerting Threshold**: > 5% of total `records_received`. High volumes indicate a severe schema drift or business rule violation upstream.

## 5. Data-Quality Failures
- **Metric**: `quality.score.overall` & `quality.failures.count`
- **Definition**: Output of the `DataQualityRun` model. Tracks Uniqueness, Validity, Completeness.
- **Alerting Threshold**: Overall score < 99.0%.

## 6. Backfill Status
- **Metric**: `backfill.progress.percentage`
- **Definition**: Monitors the execution state of manual, high-volume backfill jobs.
- **Alerting Threshold**: Backfill job stalled (0% progress over 30 minutes) or Failed status.

## Logging Strategy
All components (FastAPI, Airflow, Python Scripts) output **Structured JSON Logging**. 
This guarantees every log line contains a `correlation_id` (or `run_id`). By querying this ID in our logging tool (e.g., Google Cloud Logging), we can trace a single batch or API request completely through extraction, validation, DLQ routing, and database writes.
