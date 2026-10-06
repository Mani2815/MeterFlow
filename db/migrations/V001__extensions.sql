-- V001__extensions.sql
-- Installs required PostgreSQL extensions and creates the utility schema.
-- Executed first (alphabetical order) by docker-entrypoint-initdb.d.

-- pgcrypto provides gen_random_uuid() used in DEFAULT clauses.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- pg_stat_statements captures query statistics for performance analysis.
-- Note: requires shared_preload_libraries in postgresql.conf – already set via
-- docker compose command flags (shared_buffers). If pg_stat_statements is not
-- available, comment out this line; it is optional for Phase 1.
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Single application schema; isolates utility tables from pg_catalog.
CREATE SCHEMA IF NOT EXISTS utility;

-- ── Updated-at trigger function ───────────────────────────────────────────────
-- Attached to every table that has an updated_at column.
-- The trigger automatically sets updated_at = NOW() on every UPDATE,
-- which Datastream will capture as a CDC event in Phase 2.
CREATE OR REPLACE FUNCTION utility.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;
