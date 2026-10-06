# Utility Meter-to-Cash Cloud Data Platform

## The Problem
Modern utility companies manage massive telemetry data (smart meter readings) alongside complex financial transactions (billing and payments). Legacy relational databases struggle under the dual load of operational writes and heavy analytical queries. 

This project simulates a highly scalable, idempotent Cloud Data Platform designed to ingest operational telemetry and billing data in near real-time, enforcing strict data quality and empowering dimensional analytics.

## Architecture & Data Flow
1. **Source System**: A simulated PostgreSQL 15 operational database representing the utility CRM/Billing engine.
2. **Ingestion (CDC & Batch)**: 
   - **GCP Datastream (Phase 3)**: Agentless Change Data Capture (CDC) reads the Postgres Write-Ahead Log to capture real-time `INSERT/UPDATE/DELETE` events without impacting database performance.
   - **Python Framework (Phase 2)**: Configuration-driven batch ingestion for external REST APIs and full table loads.
3. **Processing Engine**: 
   - **Apache Beam / Dataflow (Phase 4)**: Consumes Pub/Sub notifications of new CDC files, parses JSON, dynamically normalizes payloads, and dedups events.
4. **Analytical Warehouse (Phase 5)**: 
   - **BigQuery**: Data lands in a `Staging` layer, undergoes idempotent `MERGE` logic, and populates a Dimensional Star Schema (Core) partitioned for petabyte-scale querying.
5. **Quality & Governance (Phase 6 & 7)**: 
   - **Control Plane (Phase 8)**: A FastAPI service orchestrating backfills and schema evolution.
   - **DLQ & Metrics**: Invalid records are safely quarantined in a Dead Letter Queue rather than silently dropped.

## Technology Stack
- **Database**: PostgreSQL 15 (Docker)
- **Languages**: Python 3.9, Standard SQL
- **Frameworks**: FastAPI, Apache Beam, Pytest, Pydantic
- **GCP Services**: Cloud Storage, Datastream, Pub/Sub, Dataflow, BigQuery, Cloud Run
- **Orchestration**: Apache Airflow

## Key Engineering Features
- **Idempotency**: Running pipelines twice will never duplicate data thanks to deterministic `FARM_FINGERPRINT` surrogate keys and `QUALIFY ROW_NUMBER` deduplication windows.
- **Schema Evolution**: Dynamically detects backward-compatible schema drifts (added nullable columns) while failing fast on breaking changes (type mutations).
- **Historical Backfills**: Dedicated isolation tags (`_metadata_is_backfill`) ensure historical reloads never accidentally overwrite modern CDC updates.
- **Reconciliation**: Automated SQL views ensure billed consumption mathematically matches raw meter telemetry.

## Local Setup & Testing
This repository utilizes a full local testing apparatus. No GCP credentials are required to validate the core Python/SQL logic.
```bash
# 1. Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
pip install -r dataflow/requirements.txt
pip install -r control_plane/requirements.txt

# 2. Spin up the source operational database
make db-up

# 3. Generate 100,000+ records of synthetic Utility Data
make seed

# 4. Generate simulated real-time INSERT/UPDATE/DELETE CDC events
make cdc

# 5. Run the End-to-End Test Suites (Ingestion, Beam Pipeline, Governance, Quality)
make test
```

## Documentation Directory
- `docs/architecture.md`: Initial design specifications.
- `docs/cdc-flow.md`: How Datastream and logical replication operate.
- `docs/warehouse_design.md`: Star Schema design and partitioning strategy.
- `docs/quality-framework.md`: Details on the validation and Dead Letter Queue.
- `docs/phase7-backfill-schema.md`: How we safely orchestrate backfills.
- `docs/observability-control.md`: Airflow and FastAPI Control Plane usage.
- `docs/testing.md`: The 14-scenario End-to-End test plan.
- `docs/interview-guide.md`: **Start Here** to understand the "Why" behind architectural decisions.

## GCP Setup & Cost Control
Refer to `docs/datastream-setup.md` for terraform/gcloud commands to spin up the cloud infrastructure. 
**Important:** To prevent runaway costs, ensure you drop the PostgreSQL logical replication slot when Datastream is paused, otherwise WAL logs will fill the disk. Use `make db-down -v` to destroy local volumes when finished.
