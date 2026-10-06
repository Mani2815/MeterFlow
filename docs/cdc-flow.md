# CDC Data Flow and Architecture

## Why use CDC?
Change Data Capture (CDC) is a modern data integration pattern that tracks row-level changes (INSERT, UPDATE, DELETE) in a source database and delivers them to a downstream system in near real-time. We use CDC for the Utility Meter-to-Cash platform because:
1. **Low Impact:** It reads directly from the database's Write-Ahead Log (WAL) rather than querying tables, preventing heavy operational impact on the source system.
2. **Low Latency:** Data reaches the cloud data platform in near real-time, allowing for rapid operational reporting.
3. **Delete Capture:** Unlike traditional incremental batch loads (which rely on `updated_at` timestamps), WAL-based CDC inherently captures hard `DELETE` operations.

## Primary-Key Requirements
For CDC to accurately propagate updates and deletes, the source tables **must** have a defined Primary Key (or a Unique Index). In PostgreSQL, this acts as the "Replica Identity".
- If a table lacks a Primary Key, updates and deletes cannot uniquely identify the target row downstream, which can lead to data duplication or missing updates.
- In our schema, every table (e.g., `customer_id`, `meter_id`) uses a well-defined UUID primary key.

## Representation of Operations (INSERT/UPDATE/DELETE)
Datastream wraps the raw database row inside a JSON envelope containing metadata. The downstream Cloud Storage JSON files will look similar to this:

**INSERT / UPDATE:**
```json
{
  "customer_id": "c200c821-...",
  "status": "ACTIVE",
  "_metadata": {
    "change_type": "INSERT", 
    "table": "customers",
    "schema": "utility",
    "timestamp": "2026-10-06T12:00:00Z"
  }
}
```
*Note: Datastream often represents both `INSERT` and `UPDATE` as `INSERT` or `UPDATE` depending on the configuration, but effectively they both represent an upsert operation downstream.*

**DELETE:**
```json
{
  "customer_id": "c200c821-...",
  "_metadata": {
    "change_type": "DELETE",
    "table": "customers",
    "schema": "utility"
  }
}
```
Only the primary key and the `change_type: DELETE` are strictly guaranteed to be present for a deletion event.

## Initial Snapshot vs. Ongoing Changes
When Datastream first starts, it cannot retroactively read WAL files from before it was connected.
1. **Initial Snapshot (Backfill):** Datastream issues `SELECT *` against the tables to capture the baseline state of the database. These records are written to GCS with `change_type: INSERT` (or no change type, depending on exact payload config) and a specific backfill metadata flag.
2. **Ongoing Changes:** Once the snapshot finishes, Datastream seamlessly streams live changes from the replication slot.

## Destination Cloud Storage Structure
Datastream organizes the output files in Cloud Storage automatically. The default partition structure is typically:
`gs://<bucket-name>/<prefix>/<schema>/<table>/YYYY/MM/DD/HH/MM/file.json`

## Detecting Missing Changes and Data Gaps
CDC streams can occasionally experience disruptions. To detect missing changes:
1. **Watermark / Sequence Tracking:** Datastream includes a Source Sequence Number (`_metadata.lsn`). Gaps in the LSN downstream suggest missing files.
2. **Row Count Reconciliations:** Periodically compare the `COUNT(*)` in Postgres against the materialized views in BigQuery.
3. **PK Hash Comparisons:** For exact auditing, hash the Primary Keys of a specific time window in both systems to find discrepancies.

## How to Test CDC
1. Connect to the local Postgres database.
2. Perform manual `INSERT`, `UPDATE`, and `DELETE` commands.
3. Monitor the destination GCS bucket for new JSON files.
4. Download the files and assert that the `_metadata.change_type` corresponds to the action you performed on the exact Primary Key.
(See `scripts/validate_cdc.py` for an automated test script).
