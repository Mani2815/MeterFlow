# Utility Platform Runbook

This runbook provides the operational procedures for managing and maintaining the Utility Meter-to-Cash Cloud Data Platform in production.

## 1. Daily Operations & Checks

### 1.1 Morning Health Check
1. **Check Airflow**: Log into the Airflow UI. Verify `meter_to_cash_daily_batch` succeeded. 
2. **Review Control Plane UI**: Navigate to the Overview Dashboard (`http://localhost:3000`). Check for any 'Failed Runs' or high 'DLQ Records'.
3. **Verify Data Quality**: Ensure the Data Quality score is >= 99%.

## 2. Common Operational Tasks

### 2.1 Replaying DLQ Events
1. Navigate to the **Dead Letter Queue** tab in the UI.
2. Filter for events by dataset or error type.
3. Once the upstream schema or validation issue is resolved, click **Replay Selected**.
4. Monitor the status change from `PENDING` to `PROCESSING` to `RESOLVED`.

### 2.2 Triggering a Historical Backfill
1. Navigate to the **Backfills** tab in the UI.
2. Click **Create Backfill**.
3. Supply the target `dataset` (e.g., `bills`), `start_date`, and `end_date`.
4. The system assigns an isolated `backfill_id`. Monitor progress via the progress bar.
5. **Idempotency Note**: Running a backfill over an existing date range is safe; it will UPSERT based on natural keys.

## 3. Deployment & Migrations

### 3.1 Backend & Control Plane DB Migration
Whenever `models/core.py` is updated, apply migrations:
```bash
docker-compose exec backend alembic revision --autogenerate -m "Description"
docker-compose exec backend alembic upgrade head
```

### 3.2 Cloud Run Deployment
Follow the steps in `cloud_run_deployment.md` to trigger a new build and deploy to GCP using the `control-plane-sa` service account.

## 4. Disaster Recovery
- **BigQuery Accidental Deletion**: BigQuery tables retain a 7-day snapshot (Time Travel). Use `SELECT * FROM table FOR SYSTEM_TIME AS OF ...` to recover.
- **Postgres DB Failure**: Restore the Cloud SQL Postgres instance using daily automated backups.
