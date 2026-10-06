# Dataflow CDC Pipeline (Phase 4)

This Apache Beam pipeline consumes Google Cloud Storage file notifications via Pub/Sub, parses the Datastream JSON payload, and writes canonical normalized events into BigQuery Staging.

## Pipeline Flow & Transforms Justification

1. **`ParsePubSubNotification`:**
   - **Reasoning:** Datastream writes files asynchronously. A Pub/Sub notification on GCS object finalization acts as a push-trigger. This transform reads the pub/sub envelope and extracts the `gs://bucket/name` reference.
2. **`ReadGCSFile`:**
   - **Reasoning:** Instead of using Beam's `ReadFromText` (which is typically bounded or requires polling), we dynamically fetch and stream the contents of the explicitly notified blob to support true event-driven streaming.
3. **`ParseAndNormalizeCDC`:**
   - **Reasoning:** Separates valid CDC payloads from malformed/corrupted files. It strips `_metadata`, derives the canonical fields (Table, Operation, Primary Key, Timestamp), and packages the rest into a `JSON` payload field. This provides a uniform schema in BigQuery for all upstream tables!
   - **Retry-Safe:** It relies entirely on Python JSON parsing and pure functions. It raises no external calls, making it naturally retry-safe.
4. **`GroupByKey` (Deduplication):**
   - **Reasoning:** Datastream guarantees *at-least-once* delivery. If a file is re-processed, we prevent duplicates in BQ by grouping by `(table, pk, operation)` and keeping the latest `ingestion_timestamp`.
5. **`WriteToBigQuery`:**
   - **Reasoning:** Valid records go to the Staging table for downstream dimensional modeling. Invalid records are routed to a Dead-Letter Queue (DLQ) table to ensure no data loss and allow for manual intervention.

## Metrics
The pipeline inherently tracks custom Beam metrics:
- `received_notifications`
- `files_read`
- `file_read_errors`
- `cdc_records_processed`
- `cdc_records_invalid`
