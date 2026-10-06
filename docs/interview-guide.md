# System Architecture Interview Guide

This document is designed to help data engineers and architects articulate the design decisions behind the Utility Meter-to-Cash Cloud Data Platform.

## 1. Why were these specific GCP services selected?
- **BigQuery (Data Warehouse)**: Chosen for its serverless architecture, petabyte-scale analytics capability, and separation of storage and compute. It natively supports the Medallion architecture and handles concurrent reads (dashboards) and writes (streaming) seamlessly.
- **Cloud Run (Control Plane)**: Chosen because the API is stateless, containerized (FastAPI), and experiences bursty traffic (primarily used by internal operators). Cloud Run scales to zero, saving money, while handling scale effortlessly.
- **Cloud SQL for PostgreSQL (Operational DB)**: Used to manage pipeline metadata, DLQ states, and run metrics. A transactional RDBMS ensures ACID compliance for operational state, which BigQuery (an OLAP system) is not designed for.

## 2. Why was CDC (Change Data Capture) needed?
In a utility environment, entities like Customers, Accounts, and Contracts frequently undergo updates (e.g., address changes, plan switches). Standard batch extractions often miss intermediate state changes and place heavy querying load on operational databases. CDC (via Datastream/Debezium) reads the database Write-Ahead Log (WAL), ensuring every change is captured in real-time without impacting source system performance.

## 3. Why was Pub/Sub needed?
Pub/Sub acts as a robust, asynchronous shock absorber. Meter readings come in sporadically and in massive spikes. By decoupling the source systems from the ingestion engine, Pub/Sub ensures that even if downstream processing goes down, no events are lost (thanks to message retention and acknowledgment semantics).

## 4. Why was Dataflow needed?
Dataflow (Apache Beam) provides precisely-once processing semantics, which is critical for financial/metering data. It handles the windowing of streaming Pub/Sub events, applies strict schema validation, and gracefully routes failed messages to the DLQ using side-outputs—all in real-time, which simple batch scripts cannot do.

## 5. Why was BigQuery modeled as Dimensions and Facts (Star Schema)?
- **Performance**: Joins in BigQuery are expensive. The Star Schema minimizes joins by centralizing quantitative metrics in Facts (e.g., `fact_billing`) and descriptive attributes in Dimensions (`dim_customer`).
- **Usability**: BI tools (Looker, Tableau) natively understand Star Schemas, enabling business analysts to easily drag-and-drop dimensions to slice revenue and consumption metrics without writing complex SQL.
- **Idempotency**: Using surrogate keys (`FARM_FINGERPRINT`) allows us to isolate the warehouse from source ID changes and makes UPSERT/MERGE operations straightforward and repeatable.
