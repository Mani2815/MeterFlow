# Utility Meter-to-Cash — Phase 2: Python Batch Ingestion

This builds on Phase 1 by implementing a flexible, configuration-driven Python batch ingestion framework to extract data from the PostgreSQL source system and external REST APIs into a Raw Data Lake zone.

## Key Features Implemented

1. **Configuration-Driven Extraction:** A unified `PipelineConfig` allows defining multiple `ExtractorConfig` profiles specifying data sources, endpoints, batch sizes, and incremental watermarks.
2. **PostgreSQL Extractor:** Connects to the simulated operational database, supporting both Full Loads (extracting everything) and Incremental Loads (using `updated_at` watermarks).
3. **REST API Extractor:** Connects to standard paginated REST JSON endpoints. It demonstrates built-in pagination handling via query parameters (`page`, `limit`).
4. **Resiliency and Retries:** The REST extractor uses `tenacity` for exponential backoff (e.g. recovering from simulated 500 Internal Server errors).
5. **Storage Interface (GCS & Local):** Extracted batches (raw dictionaries) are safely converted into highly-compressed `Parquet` format via `pandas/pyarrow` without destructive transformations, maintaining source fidelity. Cloud-agnostic dependency injection enables testing via `LocalStorage`.
6. **Data Organization:** Files are written automatically partitioned by data source and execution date: `data/raw/<dataset>/dt=<yyyy-mm-dd>/<run_id>_batch_N.parquet`.
7. **Idempotency & Manifests:** Each batch run generates an ingestion manifest under `_manifests/<run_id>/<dataset>.json` recording row counts, start/end times, and start/end watermarks. If a pipeline is rerun with the same `run_id`, it detects the manifest and skips safely (Idempotent execution).

## Structure
```
ingestion/
├── __init__.py
├── config.py             # Pydantic data models for configuration
├── pipeline.py           # Core ingestion orchestrator 
├── extractors/
│   ├── base.py
│   ├── postgres.py       # Handles SQL cursor streaming
│   └── rest.py           # Handles HTTP requests & pagination
└── storage/
    ├── base.py
    ├── gcs.py            # Google Cloud Storage client wrapper
    └── local.py          # Local filesystem writer for tests
```

## Running the framework

```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Run the test suite that proves all requirements
pytest tests/test_ingestion.py -v

# Run an example extraction pipeline
python scripts/run_ingestion.py
```
