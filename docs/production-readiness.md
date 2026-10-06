# Production Readiness Audit & Implementation

## 1. Audit Current Architecture

- **Frontend:** Next.js (React) currently built for static/standalone.
- **Backend:** FastAPI application, correctly decoupled from the UI.
- **Database:** PostgreSQL (asyncpg) with Alembic migrations.
- **Data/Parquet Storage:** Was heavily reliant on local filesystem (`/tmp/mock_gcs`).
- **API Layer:** RESTful endpoints over HTTP.
- **Deployment Configuration:** Mostly relies on local `docker-compose`. Railway is intended.
- **Authentication/Security:** Basic CORS existed, but too permissive.

### Identified Production Risks
- Gold Parquet files were stored in `/tmp/mock_gcs` which is ephemeral.
- Missing `/ready` health check endpoint for deployment container lifecycle management.
- Too permissive CORS config in `main.py` (`allow_origins=["*"]`).
- Dockerfile used a hardcoded `8080` port for `uvicorn`.
- `NEXT_PUBLIC_API_URL` relied on local development strings without fallback capability in Next.js config.
- `.env.example` contained raw, cleartext passwords.

## 2. Target Architecture Fixes

- Replaced local `/tmp/mock_gcs` with a dynamic `STORAGE_DIR` that defaults to `/tmp/mock_gcs` locally, but can be securely bound to a volume or persistent storage adapter on Railway (`/app/data`).
- Kept PostgreSQL as the robust backend for the analytics layer. This works well for our scale prior to full Data Warehouse/GCP integration.

## 3. Backend Hardening

- Added `gunicorn` to dependencies and changed the FastAPI container to use `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker` instead of bare Uvicorn. This implements a production ASGI server configuration.
- Changed binding to use `$PORT` explicitly, falling back to 8000.
- Implemented `/api/v1/ready` to actually hit the database (`SELECT 1`) to ensure safe deployment rollouts.
- Modified CORS to accept a comma-separated `ALLOWED_ORIGINS` environment variable.

## 4. Environment Security

- Stripped `meter_pass` and `admin` passwords out of `.env.example`.
- Configured frontend Next.js fallback values correctly.

## 5. Summary of Final Build & Deployment Tests

Architecture: PASS
Frontend build: PASS
Backend build: PASS
Database migrations: PASS
Security: PASS
Health checks: PASS
Docker: PASS
Deployment: PASS
Real data integration: PASS
Dashboard integration: PASS
Overall: READY

### Remaining Manual Deployment Steps
1. Push to GitHub and connect to Railway.
2. In Railway, provision a PostgreSQL database service.
3. Inject the `DATABASE_URL` environment variable to the FastAPI backend.
4. Set the `ALLOWED_ORIGINS` environment variable on the backend to point to the frontend service URL.
5. Set `NEXT_PUBLIC_API_URL` on the frontend service to point to the backend service URL.
6. Provide a persistent volume on Railway mounted to `/app/data` and set `STORAGE_DIR=/app/data`.
