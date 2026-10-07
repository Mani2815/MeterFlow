# MeterFlow Data Console

This is a Next.js application that provides the front-end dashboard for the MeterFlow Utility Data Platform.

## Features

- **Dashboard**: High-level metrics for data pipelines and master data.
- **Pipelines**: Monitor data ingestion, standardization, and quality checks.
- **Data Quality & DLQ**: Review data quality metrics and quarantined records.
- **Master Data**: Browse synthetic utility entities like Customers, Accounts, Meters, Contracts, and Service Points.
- **Data Models**: Explore the star schema definitions.

## Operational Modes

The frontend supports two distinct modes of operation, controlled by the `NEXT_PUBLIC_DATA_MODE` environment variable.

### 1. API Mode (Live)
In this mode, the frontend acts as a standard Single Page Application (SPA), fetching data live from the FastAPI backend and PostgreSQL database.

```bash
NEXT_PUBLIC_DATA_MODE=api npm run dev
```

### 2. Demo Mode (Static/Snapshot)
In this mode, the frontend bypasses the FastAPI backend entirely. It reads pre-generated static JSON snapshots located in `public/data/`. This is designed for simple, zero-infrastructure hosting (e.g., Vercel) where you only want to demonstrate the UI and pipeline results without running a Python backend or Postgres instance.

```bash
NEXT_PUBLIC_DATA_MODE=demo npm run dev
```

*Note: You must generate the JSON snapshots using `scripts/generate_demo_data.py` from the root directory before running in demo mode.*

## Getting Started

First, install dependencies:

```bash
npm install
```

Then, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Deployment

To deploy this statically on Vercel:

1. Ensure your snapshots in `public/data/` are up to date.
2. Set `NEXT_PUBLIC_DATA_MODE=demo` in your Vercel Environment Variables.
3. Deploy! Vercel will serve the application with zero backend dependencies.
