# MeterFlow: Utility Meter-to-Cash Data Platform

MeterFlow is an end-to-end data platform demonstrating the ingestion, processing, and visualization of utility smart meter telemetry alongside synthetic master data.

## Architecture

This project is built as a complete, locally executable stack without external cloud dependencies:

1. **Data Pipeline (Python/Pandas/PyArrow)**
   - **Ingestion**: Fetches the UK Power Networks (UKPN) SmartMeter dataset and stores it as Raw JSON chunks.
   - **Standardization**: Cleanses and normalizes the data into Standardized Parquet files.
   - **Data Quality**: Validates records, separating valid rows into **Gold Parquet** while quarantining bad records into a Dead Letter Queue (DLQ).

2. **Control Plane (PostgreSQL 15)**
   - Stores synthetic master data (Customers, Accounts, Contracts, Meters, Service Points).
   - Tracks pipeline execution metadata and data quality metrics.

3. **Backend API (FastAPI)**
   - Provides REST endpoints to expose pipeline metadata and synthetic master data to the frontend.

4. **Frontend Dashboard (Next.js)**
   - A modern web console (`/ui`) that visualizes data pipelines, schemas, and data quality metrics.
   - Features two operational modes:
     - **API Mode**: Connects live to the FastAPI backend and Postgres.
     - **Demo Mode**: A static, frontend-only mode that reads generated JSON snapshots, suitable for Vercel deployment without a running backend.

## Local Setup

### 1. Prerequisites

- Docker and Docker Compose
- Node.js (>=20.9.0)
- Python 3.9+

### 2. Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
# Alternatively, if dependencies are locally scattered:
pip install fastapi uvicorn sqlalchemy asyncpg pandas pyarrow google-cloud-storage python-json-logger httpx
```

Ensure you have a `.env` file at the root. You can copy `.env.example` if available.

### 3. Start the Infrastructure

```bash
# Start PostgreSQL and FastAPI backend
docker compose up -d
```

*Note: The frontend can also be run via Docker, or run locally for active development.*

### 4. Run the Data Pipeline

Process the UKPN SmartMeter dataset locally (target size configured via `NUM_METER_READINGS` in `.env`):

```bash
# 1. Ingestion
PYTHONPATH=backend python backend/app/ingestion/smartmeter.py source smartmeter --mode test

# 2. Standardization (Use the Ingestion Run ID output from the previous step)
PYTHONPATH=backend python backend/app/processing/standardize.py run smartmeter --ingestion-run-id <YOUR_INGESTION_RUN_ID>

# 3. Data Quality (Use the Standardize Run ID output from the previous step)
PYTHONPATH=backend python backend/app/processing/quality.py run --standardize-run-id <YOUR_STANDARDIZE_RUN_ID>
```

### 5. Start the Frontend Dashboard

```bash
cd ui
npm install

# Run in live API mode
NEXT_PUBLIC_DATA_MODE=api npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the MeterFlow console.

## Generating Demo Data (Static Mode)

To deploy the frontend statically (without the Python/Postgres backend), generate static JSON snapshots from your processed Gold Parquet files and Postgres master tables:

```bash
# Ensure backend and postgres are running
PYTHONPATH=backend python scripts/generate_demo_data.py
```

This will write JSON snapshots into `ui/public/data/`. You can then run the frontend in demo mode:

```bash
cd ui
NEXT_PUBLIC_DATA_MODE=demo npm run dev
```
