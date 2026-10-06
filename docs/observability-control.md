# Observability and Control Plane Architecture

## 1. The FastAPI Control Plane (Deployable to Cloud Run)
A lightweight FastAPI service acts as the operational control plane to trigger jobs, check statuses, and query pipeline health.

### Cloud Run Deployment
This service is fully containerized and uses 12-factor app principles. It expects no secrets in the source code.
**To deploy to GCP:**
```bash
gcloud builds submit --tag gcr.io/[PROJECT_ID]/meter-control-plane
gcloud run deploy meter-control-plane \
    --image gcr.io/[PROJECT_ID]/meter-control-plane \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars="LOG_LEVEL=INFO"
```

**To run locally:**
```bash
docker build -t meter-control-plane ./control_plane
docker run -p 8080:8080 meter-control-plane
```

### 2. Airflow Orchestration (Batch Workflow)
As requested, we avoid expensive managed orchestration unless necessary (e.g., Cloud Composer). Airflow can be run locally or within a dedicated compute container.

The DAG `meter_to_cash_batch_pipeline` strictly defines the boundaries:
`Extract -> Validate -> Load -> Transform -> Quality -> Reconciliation`

- **Retries & Failure Handling**: Default arguments enforce 3 retries with 5-minute exponential backoffs to handle transient extraction failures.
- **Dependencies**: The pipeline will immediately halt if `Validate` fails, preventing corrupt data from ever entering the `Transform` layer.

## 3. Observability & Monitoring
A comprehensive data platform requires complete visibility. We track the following metrics via BigQuery tables (`meter_to_cash_quality.batch_metrics`), FastAPI responses, and Dataflow metrics:

- **Pipeline Latency**: Captured inherently by Airflow task execution times and the `execution_time_seconds` metric in `batch_metrics`.
- **Records Processed vs Rejected**: Recorded per batch via the Validation script and queried at `/quality/latest`.
- **DLQ Volume**: Handled by tracking `COUNT(*)` in `dead_letter_queue` over time. Spikes indicate an upstream schema breakage.
- **Data-Quality Failures**: Categorized in the DLQ to identify which business rules fail most often.
- **Backfill Status**: Controlled dynamically by polling the `GET /runs/{run_id}` endpoint.
