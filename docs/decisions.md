# Architectural Decisions: Utility Meter-to-Cash Cloud Data Platform

Each decision record (ADR) follows the format: **Context → Decision → Rationale → Trade-offs → Alternatives Rejected**.

---

## ADR-001: Use PostgreSQL as the Simulated OLTP Source

**Status:** Accepted

**Context:**
We need a relational OLTP database to simulate a utility CRM/billing system and to demonstrate
real CDC ingestion using Datastream.

**Decision:**
Use PostgreSQL (containerized via Cloud Run or Docker) with `wal_level = logical` enabled.

**Rationale:**
- Datastream natively supports PostgreSQL logical replication.
- PostgreSQL is free, well-documented, and widely used in student projects.
- Faker + SQLAlchemy can seed realistic synthetic data quickly.
- Logical replication produces `INSERT`/`UPDATE`/`DELETE` events that are more realistic
  than timestamp-based incremental polling.

**Trade-offs:**
- Requires `wal_level = logical` configuration, which is non-default and must be set in
  the container's `postgresql.conf`.
- Cloud Run is not ideal for stateful workloads; for simplicity, the DB may run locally
  during development and only CDC is pushed to GCP.

**Alternatives Rejected:**
- **MySQL:** Datastream supports it, but PostgreSQL is more familiar and has better tooling.
- **SQLite:** Does not support logical replication.
- **Spanner:** Overkill and not free-tier-friendly.

---

## ADR-002: Use Datastream for CDC, Not Timestamp Polling

**Status:** Accepted

**Context:**
Master-data entities (Customer, Account, Contract, Service Point, Meter) need to be
incrementally synchronized whenever the source OLTP record changes.

**Decision:**
Use GCP Datastream (log-based CDC) rather than timestamp-based incremental polling.

**Rationale:**
- Log-based CDC captures `DELETE` events, which timestamp polling cannot detect.
- No modifications are needed on the source schema (no need to add `updated_at` triggers).
- Datastream is fully managed — no polling infrastructure to maintain.
- Demonstrates a real enterprise CDC pattern.

**Trade-offs:**
- Requires PostgreSQL logical replication to be enabled; adds setup complexity.
- Datastream has a cost per GB of data streamed (mitigated at low simulated volumes).
- Datastream writes Avro to GCS, requiring a downstream Dataflow job to parse into BigQuery.

**Alternatives Rejected:**
- **Debezium on Kafka:** Powerful, but introduces Kafka infrastructure far beyond a single-student
  budget and scope. Not available as a managed GCP service.
- **Timestamp watermark polling:** Simpler but misses deletes and has edge cases around
  transactions that land before the watermark is checked.

---

## ADR-003: Use Pub/Sub + Dataflow Streaming for Meter Readings

**Status:** Accepted

**Context:**
Meter readings are high-frequency events (one per meter per 15 minutes for AMI meters).
They arrive continuously and need to be landed in BigQuery with low latency.

**Decision:**
- AMI simulator publishes JSON messages to a Cloud Pub/Sub topic.
- A Dataflow Streaming job (Apache Beam / Python SDK) reads from the subscription,
  validates the schema, and writes to `raw.meter_reading`.
- A dead-letter Pub/Sub topic captures unparse-able messages.

**Rationale:**
- Pub/Sub is the idiomatic GCP fan-out messaging system; it decouples the AMI simulator
  from the processing pipeline.
- Dataflow Streaming with Apache Beam provides exactly-once semantics (via Beam's
  `BigQueryIO` with `FILE_LOADS` or streaming inserts).
- The pattern is portable and demonstrates a production-grade streaming architecture.

**Trade-offs:**
- Dataflow streaming workers have a minimum cost even at low message rates; mitigated by
  using `e2-medium` and autoscaling min=1.
- Exactly-once semantics with `STREAMING_INSERTS` requires deduplication logic; we handle
  this by using `reading_id` as the BigQuery dedup key.

**Alternatives Rejected:**
- **Dataflow direct write from Pub/Sub without validation:** Skips the DQ layer, producing
  dirty data in the raw table.
- **BigQuery Storage Write API direct from publisher:** Tighter coupling, loses the
  message-at-a-time visibility and dead-letter capability.
- **Cloud Functions consumer:** Scales to zero but has per-invocation cold-start latency
  incompatible with high-frequency readings.

---

## ADR-004: Use Batch File Drop (GCS) for Billing and Payment Data

**Status:** Accepted

**Context:**
Billing and payment records are produced by separate simulated engines on a periodic schedule
(e.g., nightly billing run, daily payment reconciliation). They are not a continuous stream.

**Decision:**
- Simulators write Parquet (billing) and CSV (payment) files to GCS buckets.
- Cloud Scheduler triggers a Cloud Run job every 30 minutes to detect new files.
- The Cloud Run job submits a Dataflow batch job per new file.
- A processed-files manifest in GCS prevents re-processing.

**Rationale:**
- Batch file drops are a very common enterprise integration pattern; demonstrating it is valuable.
- Parquet for billing (structured, typed, compressed) and CSV for payments (simulates a more
  primitive payment processor) demonstrates handling of different file formats.
- The manifest pattern is a simple, cost-free idempotency mechanism.

**Trade-offs:**
- If Cloud Scheduler or the Cloud Run trigger fails, files may be delayed but not lost.
- The manifest is a single GCS object and could be a bottleneck at very high file volumes
  (not a concern at simulated scale).

**Alternatives Rejected:**
- **GCS Object Notifications → Pub/Sub → Cloud Run:** More real-time but adds complexity;
  unnecessary given billing/payment are inherently batch.
- **Datastream from a billing DB:** The billing engine is simulated as a file export,
  not a persistent database, making Datastream inapplicable.

---

## ADR-005: Three-Layer BigQuery Architecture (Raw → Staging → Warehouse)

**Status:** Accepted

**Context:**
We need a clear separation between landed raw data, cleaned/typed data, and the authoritative
historized warehouse.

**Decision:**
Use four BigQuery datasets: `raw`, `staging`, `warehouse`, `marts`.

**Rationale:**

| Layer | Purpose |
|-------|---------|
| `raw` | Immutable audit trail. If a bug is introduced in staging or warehouse logic, we can replay from raw. |
| `staging` | Typed, cleaned, deduplicated, PII-pseudonymized. Acts as a quality-verified input to the warehouse. |
| `warehouse` | SCD2 dimensions + append-only facts. The single source of truth for all analytics. |
| `marts` | Pre-aggregated, business-facing tables and views. Separates heavy aggregation from raw querying. |

**Trade-offs:**
- Adds storage cost vs. a two-layer approach. Mitigated by partition expiry on raw tables.
- More transformation steps = more pipelines to maintain.

**Alternatives Rejected:**
- **Two-layer (raw + warehouse):** Loses the ability to independently audit staging
  transformations and makes PII boundary management harder.
- **Single-layer (warehouse only):** No replay capability; dangerous for a production-grade design.
- **Data Vault 2.0:** Powerful but significantly more complex to implement and explain;
  disproportionate for a student portfolio project.

---

## ADR-006: SCD Type 2 for Slowly Changing Dimensions

**Status:** Accepted

**Context:**
Dimensions like Customer and Contract change over time (e.g., customer changes email,
contract tariff is renegotiated). Analytics must be able to attribute historical bills to
the tariff that was in effect at the time.

**Decision:**
Use SCD Type 2 with `valid_from`, `valid_to`, and `is_current` columns on dimension tables.

**Rationale:**
- SCD2 is the industry-standard approach for preserving dimension history in a Kimball warehouse.
- It allows point-in-time joins: `JOIN dim_customer ON customer_id = customer_id AND bill_date BETWEEN valid_from AND COALESCE(valid_to, '9999-12-31')`.
- Straightforward to implement with BigQuery `MERGE` statements.

**Trade-offs:**
- Queries are slightly more complex (must filter on `is_current` or use date-range joins).
- Surrogate keys must be generated (handled by a BigQuery sequence or UUID).

**Alternatives Rejected:**
- **SCD Type 1 (overwrite):** Loses history. A bill from 3 months ago would appear under
  the customer's current tariff, not the one at bill time.
- **SCD Type 6 (hybrid):** More powerful but significantly more complex; deferred to a
  future iteration.

---

## ADR-007: Use Cloud Run for the Data Quality Service

**Status:** Accepted

**Context:**
Data quality checks need to be applied after staging and before writing to the warehouse.
The checks include cross-table referential integrity checks that require BigQuery access.

**Decision:**
Implement a Python-based DQ service deployed on Cloud Run (job mode, not always-on).
The service is invoked by Cloud Scheduler after each staging pipeline completes.

**Rationale:**
- Cloud Run jobs are billed per CPU-second of execution, with no idle cost.
- Python provides flexibility to implement custom DQ rules using BigQuery client library.
- Running DQ as a separate Cloud Run job creates a clear quality gate between staging and warehouse.
- Logs and metrics can be emitted to Cloud Logging / Cloud Monitoring using structured JSON.

**Trade-offs:**
- Cold start latency on Cloud Run (mitigated by minimum 1 instance during business hours).
- If the DQ service fails mid-run, the batch is partially processed; mitigated by atomic
  BigQuery `MERGE` statements within each rule group.

**Alternatives Rejected:**
- **Great Expectations (open-source):** Adds a heavy dependency and complex configuration for
  a portfolio project; custom rules are more transparent.
- **dbt tests:** dbt is excellent for warehouse-layer testing but not suited for streaming
  ingestion quality gates. May be added as a future iteration.
- **Dataflow DQ inline:** Merging DQ into the Dataflow pipeline increases job complexity and
  makes it harder to update rules without redeploying the Dataflow job.

---

## ADR-008: Pseudonymize PII in Staging, Restrict Raw Access

**Status:** Accepted

**Context:**
Customer PII (name, email, phone, date of birth) must not be exposed to analytics consumers.
The raw layer must preserve the original data for audit and replay purposes.

**Decision:**
- Raw layer: PII stored as-is. Access restricted to `sa-dataflow` service account only;
  no human IAM bindings on the `raw` dataset.
- Staging layer: PII columns replaced with SHA-256 hashes. `date_of_birth` reduced to year only.
- Warehouse/marts: Only hashed PII or non-PII attributes exposed.

**Rationale:**
- SHA-256 pseudonymization is deterministic, allowing joins on `email_hash` across tables
  without exposing the original value.
- This approach is proportionate to a simulated project while demonstrating the correct
  enterprise data governance mindset.

**Trade-offs:**
- SHA-256 hashes are theoretically reversible with a rainbow table for common values like
  email addresses. In a real system, HMAC-SHA-256 with a secret key (stored in Secret Manager)
  would be used. This is noted as a future improvement.

**Alternatives Rejected:**
- **Encrypt PII with AEAD (BigQuery native):** More secure but requires key management via
  Cloud KMS; adds cost and complexity beyond project scope.
- **Remove PII entirely from raw:** Loses the ability to re-pseudonymize if the hashing
  strategy changes.

---

## ADR-009: Partition by Ingestion Date, Cluster by Natural Key

**Status:** Accepted

**Context:**
BigQuery charges by bytes scanned. Without partitioning and clustering, full table scans
on large fact tables would be expensive.

**Decision:**
- All raw and staging fact tables are partitioned by `DATE(read_at)`, `bill_date`, or `payment_date`.
- All tables are clustered by the primary natural key (`meter_id`, `account_id`, etc.).
- Warehouse dimension tables are NOT partitioned (they are small; partitioning adds overhead).

**Rationale:**
- Partition pruning limits scans to the relevant date range.
- Clustering further reduces scan size when filtering by the entity key.
- Together they can reduce query costs by 80–95% on typical analytical queries.

**Trade-offs:**
- Partitioned tables require `WHERE partition_date BETWEEN ...` in queries to benefit from pruning.
- Clustering is approximate; not all queries will benefit.

---

## ADR-010: Use Cloud Scheduler as the Orchestrator (Not Airflow / Composer)

**Status:** Accepted

**Context:**
Pipeline jobs (Dataflow batch, Cloud Run DQ, BigQuery scheduled queries) need to be triggered
on a schedule and in the correct order.

**Decision:**
Use Cloud Scheduler for cron-based triggering. Dependencies between stages are enforced by
having each step check a GCS manifest or BigQuery metadata table before proceeding.

**Rationale:**
- Cloud Scheduler is free (up to 3 jobs) and requires zero infrastructure.
- Simple DAG-style dependencies can be encoded in the Cloud Run job logic.
- Cloud Composer (managed Airflow) costs ~$300/month minimum — not feasible for a student project.

**Trade-offs:**
- No visual DAG UI or retry-with-backoff built-in (Cloud Scheduler retries are limited).
- For complex multi-step dependencies, this approach is fragile; Airflow would be preferred
  in production.

**Future Improvement:**
If the project is extended, replace Cloud Scheduler with Cloud Composer (Airflow) or
Prefect Cloud (has a generous free tier) for proper DAG-based orchestration with
retry policies, SLA monitoring, and task-level observability.

---

## ADR-011: Keep Platform Single-Region (us-central1)

**Status:** Accepted

**Context:**
Multi-region deployments improve availability and latency but add significant cost and complexity.

**Decision:**
Deploy all GCP resources in `us-central1` only.

**Rationale:**
- Single-region reduces egress costs (no cross-region data transfer).
- `us-central1` has the broadest GCP service availability.
- For a portfolio project demonstrating data engineering skills, HA/DR is out of scope.

**Trade-offs:**
- No regional failover.
- BigQuery datasets in a single region cannot be queried from other regions without cost.

**Alternatives Rejected:**
- **Multi-region BigQuery dataset:** Adds cost; unnecessary for a simulated workload.
