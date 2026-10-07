# Frontend Deployment (Vercel)

This repository supports deploying the frontend as a completely static, data-driven demo to Vercel without requiring the Python/PostgreSQL backend to be running.

## Demo Mode

The frontend can read static JSON snapshots that are generated directly from the validated Gold Parquet zone.

1. Ensure you have run the backend ingestion pipeline to generate the Gold data.
2. Run the generation script:
   ```bash
   python scripts/generate_demo_data.py
   ```
3. Set the environment variable in Vercel (or your local `.env.local`):
   ```env
   NEXT_PUBLIC_DATA_MODE=demo
   ```
4. Build and deploy to Vercel. 
   - No backend will be requested.
   - The UI will read from `/data/*.json`.
   - A banner will indicate the demo snapshot mode.

## Local Development (API Mode)

For local development with the real backend, either unset `NEXT_PUBLIC_DATA_MODE` or set it to:

```env
NEXT_PUBLIC_DATA_MODE=api
```

This causes the frontend to fetch directly from `http://localhost:8000/api/v1` and connects it to the real FastAPI and PostgreSQL control plane.
