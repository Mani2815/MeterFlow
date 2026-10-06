-- V004__replication.sql
-- Sets up PostgreSQL logical replication for CDC via Datastream (Phase 2).
--
-- A PUBLICATION makes all utility.* tables eligible for WAL-based replication.
-- The replication slot is intentionally LEFT COMMENTED OUT here because a slot
-- holds WAL indefinitely until a consumer connects.  Create it when Datastream
-- is configured in Phase 2 to avoid unbounded disk growth.
--
-- Quick reference for Phase 2:
--   SELECT pg_create_logical_replication_slot('datastream_slot', 'pgoutput');
--   SELECT * FROM pg_replication_slots;                     -- verify
--   SELECT pg_drop_replication_slot('datastream_slot');     -- tear down

-- Publish all current and future tables in the utility schema.
-- Datastream will filter to the tables it is configured to stream.
CREATE PUBLICATION meter_to_cash_pub
    FOR ALL TABLES
    WITH (publish = 'insert, update, delete, truncate');

-- Grant the replication role to the application user so Datastream can
-- authenticate with standard credentials (no superuser needed).
-- In Phase 2 replace 'meter_user' with a dedicated Datastream service account.
ALTER USER meter_user REPLICATION;

-- Verification queries (run these after Phase 2 Datastream setup):
--   SELECT pubname, puballtables FROM pg_publication;
--   SELECT slot_name, plugin, active FROM pg_replication_slots;
--   SELECT schemaname, tablename FROM pg_publication_tables WHERE pubname = 'meter_to_cash_pub';
