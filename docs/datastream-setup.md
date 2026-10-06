# Datastream Configuration and Setup Guide

This document outlines the step-by-step process for configuring Google Cloud Datastream to capture Change Data Capture (CDC) events from our simulated PostgreSQL utility database and land them in Google Cloud Storage.

## 1. Source Database Preparation (PostgreSQL)

Before Datastream can extract CDC events, the source PostgreSQL instance must be configured for logical replication. 
In our Docker setup (Phase 1), this is already done via the `docker-compose.yml` command parameters:

- `wal_level = logical`: Ensures the Write-Ahead Log (WAL) contains the information needed for logical decoding.
- `max_replication_slots`: Sufficient slots must be available (e.g., 10).
- `max_wal_senders`: Must equal or exceed the number of slots.

**Database-level configuration:**
```sql
-- Create a publication that covers all tables in our schema
CREATE PUBLICATION meter_to_cash_pub FOR ALL TABLES WITH (publish = 'insert, update, delete, truncate');

-- (Optional) Create a dedicated replication user
CREATE USER datastream_user WITH REPLICATION PASSWORD 'SECURE_PASSWORD';
GRANT USAGE ON SCHEMA utility TO datastream_user;
GRANT SELECT ON ALL TABLES IN SCHEMA utility TO datastream_user;
```

## 2. Setting Up GCP Resources

### Step 2a: Create Cloud Storage Destination
Create a regional bucket to hold the raw CDC files.
```bash
gcloud storage buckets create gs://meter-cdc-raw-bucket \
    --location=us-central1 \
    --uniform-bucket-level-access
```

### Step 2b: Create Datastream Connection Profiles

**Source Profile (PostgreSQL):**
You must create a Connection Profile for the PostgreSQL database. Since our database is local, you might need to use `ngrok`, a VPN, or Datastream's proxy network settings to allow GCP to reach your local instance. For a true GCP environment, Cloud SQL is typically used.
- Type: PostgreSQL
- Host / Port: `<YOUR_PUBLIC_IP>` / 5432
- Username / Password: (Use a dedicated replication user)

**Destination Profile (GCS):**
- Type: Google Cloud Storage
- Bucket: `meter-cdc-raw-bucket`
- Path Prefix: `/datastream/`

### Step 2c: Create the Datastream Stream
When configuring the stream:
1. **Select Profiles:** Choose the Source (Postgres) and Destination (GCS) profiles.
2. **Select Objects:** Include the `utility` schema (e.g., `customers`, `accounts`, `meter_readings`).
3. **Replication Slot:** Provide a slot name (e.g., `datastream_cdc_slot`) and publication name (`meter_to_cash_pub`).
4. **Format:** Choose JSON format (JSONL). This makes it easier to parse downstream.
5. **Backfill Mode:** Choose Automatic. Datastream will first take a historical snapshot of all existing data, and then transition seamlessly into streaming real-time WAL changes.

## 3. Configuration Templates
A template configuration file (`configs/datastream_config.template.yaml`) is provided in this repository to script this setup using Terraform or the gcloud CLI.

## 4. Cleanup Instructions
To stop incurring charges and clean up resources:
1. Pause the Datastream stream.
2. Delete the Datastream stream.
3. Delete the Source and Destination connection profiles.
4. Drop the replication slot on PostgreSQL to prevent WAL accumulation:
   ```sql
   SELECT pg_drop_replication_slot('datastream_cdc_slot');
   ```
5. Delete the Cloud Storage bucket (if no longer needed).
