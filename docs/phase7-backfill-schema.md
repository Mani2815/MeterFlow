# Phase 7: Backfills and Schema Evolution

## 1. Schema Evolution & Governance
Managing upstream database changes is critical to prevent downstream silent data corruption or pipeline crashes.

### Detection Mechanism (`governance/schema_registry.py`)
- The `SchemaRegistry` dynamically intercepts schemas.
- **Backward Compatible Changes**: When a new column is added, it assumes it is nullable. It updates the internal representation, increments the schema minor version (e.g., `1.0` -> `1.1`), and allows the pipeline to continue. Older records are treated as having `NULL` for the new field.
- **Incompatible Changes**: If a field is *removed* or its *data type changes* (e.g., `INT` to `STRING`), the registry intentionally throws an `IncompatibleSchemaError`.
- **Failure Behavior**: An incompatible change hard-fails the pipeline. This is a deliberate "Fail Fast" design choice to prevent writing malformed strings into a strictly typed BigQuery `INT64` column, which would permanently break the Star Schema.

## 2. Historical Backfills
Occasionally, logic changes or data is lost, requiring us to reread older data from the operational source.

### Backfill Manager (`governance/backfill_manager.py`)
- **Isolation**: Backfills use a distinct `run_id` (e.g., `bf_2026_retro`) and attach metadata tags (`_metadata_is_backfill: true`) directly to the payloads. This clearly distinguishes backfill data from live CDC data in the warehouse.
- **Configurability**: Engineers specify explicit `start_date` and `end_date` bounds to prevent accidentally querying 10 years of data.
- **Idempotency**: Before execution, the manager checks `data/raw/_manifests/<run_id>/<table_name>_backfill.json`. If a successful run is logged, reruns are safely `SKIPPED`.
- **Warehouse Safety**: Because the BigQuery layer (Phase 5) uses `QUALIFY ROW_NUMBER() OVER(PARTITION BY ... ORDER BY ingestion_timestamp DESC)` and `MERGE` statements on primary keys, backfilled data automatically deduplicates. If a backfilled record is older than the current Core record, the `MERGE` condition (`S.event_timestamp >= T.bq_update_timestamp`) ensures the older backfill data doesn't overwrite a newer live update!

### Validation & Reconciliation
Following a backfill, the Phase 6 `batch_metrics` logic captures precisely how many records were extracted. The warehouse `vw_recon_meter_to_bill` reconciliation script must be executed to ensure that injecting historical meter readings did not negatively warp the expected billed consumption baseline.
