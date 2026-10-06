# Current State Audit

This audit evaluates the current state of the Utility Meter-to-Cash Cloud Data Platform repository, identifying the gap between the prototype and a real, working, deployment-ready end-to-end application.

## 1. Overview
1. **Frontend framework/version**: Next.js App Router with TypeScript, Tailwind CSS, Lucide React, and Recharts.
2. **Backend existence**: A rudimentary FastAPI prototype exists in `control_plane/main.py`.
3. **Current API routes**:
   - `GET /health`
   - `POST /ingestion/run`
   - `POST /backfill`
   - `GET /runs/{run_id}`
   - `GET /quality/latest`

## 2. Hardcoded / Fake Data Sources (Frontend)
Almost all data currently displayed in the frontend is hardcoded directly within the React components. There is no API integration yet.
- **Hardcoded Arrays**:
  - `chartData` (`ui/src/app/page.tsx`)
  - `PIPELINES` (`ui/src/app/pipelines/page.tsx`)
  - `ISSUES` and `chartData` (`ui/src/app/data/quality/page.tsx`)
  - `DLQ_EVENTS` (`ui/src/app/data/dlq/page.tsx`)
  - `BACKFILLS` (`ui/src/app/data/backfills/page.tsx`)
  - `SOURCES` (`ui/src/app/data/sources/page.tsx`)
  - `EVENTS` (`ui/src/app/data/cdc/page.tsx`)
  - `latencyData` (`ui/src/app/operations/monitoring/page.tsx`)
  - `consumptionByRegion` and `revenueTrend` (`ui/src/app/business/analytics/page.tsx`)
  - `chartData` (`ui/src/app/business/meter-to-cash/page.tsx`)
- **Fake Metrics**: All KPIs (e.g., "18.4M Records", "99.7% Quality Score", "1.24M Events Today") are static JSX elements.
- **Fake Status Values**: Hardcoded strings like `"Healthy"`, `"Processed"`, `"Warning"`.
- **Fake Timestamps**: Hardcoded strings like `"10:42:31"`, `"2 min ago"`.
- **Fake Pipeline History**: Hardcoded runs like `RUN-20261006-1042`.
- **Fake Warehouse Schemas**: `SchemaRow` components in `warehouse/explorer/page.tsx` are manually typed out.
- **Fake Data Model**: The Star Schema visualization is purely presentational JSX.

## 3. Hardcoded / Fake Data Sources (Backend)
- The FastAPI backend uses an in-memory dictionary (`_runs_db: Dict[str, Dict[str, Any]] = {}`) to simulate state.
- `GET /quality/latest` returns a hardcoded JSON response.
- There is no database connection, no GCP SDK usage, and no real API contracts.

## 4. Infrastructure & Configuration
- **Existing environment configuration**: No standard `.env.example` or `.env.local` files exist.
- **Existing Docker configuration**: A basic `control_plane/Dockerfile` exists. There is no `docker-compose.yml` for unified local execution and no frontend Dockerfile.
- **Existing deployment configuration**: Some documentation exists in `docs/observability-control.md` for Cloud Run, but no CI/CD pipelines (e.g. GitHub Actions) exist.
- **Existing database/schema**: A local PostgreSQL database is orchestrated via a Makefile (`make db-up`), but it is meant for operational data simulation (Phase 1), not for Control Plane metadata.
- **Reusable UI components**: Many components (`MetricCard`, `DagNode`, `StatusBadge`) are defined inline within the specific page files instead of a shared `components/` directory.
- **Authentication/Authorization**: None exists. All routes are unprotected.
- **Unused dependencies**: None identified. All installed frontend dependencies are actively used for the prototype layout.

## Conclusion
The UI provides an excellent visual foundation, but it is currently a "shell". The backend is a placeholder. To make this production-ready, we must build a robust FastAPI backend connected to a Control Plane PostgreSQL database and BigQuery, define strict OpenAPI contracts, build a React Query/fetch data-access layer in the frontend, and replace every hardcoded constant with live API state.
