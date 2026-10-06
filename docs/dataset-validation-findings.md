# Dataset Validation Findings

This document outlines the issues discovered during the end-to-end dataset audit of the Utility Meter-to-Cash Cloud Data Platform.

| Finding | Severity | Evidence | Affected component | Expected behavior | Actual behavior | Recommended fix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Warehouse Loading Gap** | CRITICAL | `audit.py` shows Parquet files in `/tmp/mock_gcs/utility/gold/` but no downstream queries or BigQuery insertion logic. | `backend/app/processing`, Data Warehouse | Gold data should be loaded into BigQuery / PostgreSQL Analytics tables automatically. | Processing stops at Parquet generation. | Implement Phase 5 to load Gold Parquet into the Warehouse (BigQuery). |
| **Hardcoded UI Analytics Data** | CRITICAL | `ui/src/app/console/page.tsx` and `ui/src/app/console/business/meter-to-cash/page.tsx` use static `chartData` arrays. | Frontend Analytics | UI displays real aggregated data from the Warehouse. | UI renders fabricated static metrics. | Connect UI charts to real backend API endpoints querying the Warehouse. |
| **Fake CDC / Operational Data** | HIGH | `ui/src/app/console/data/cdc/page.tsx` contains hardcoded `MTR-`, `BILL-`, and `CUST-` events. | Frontend Data CDC View | Operational CDC view should reflect real `Debezium`/`Datastream` events or database triggers. | UI renders static array of fake events. | Wire CDC pages to real event streams or remove dummy pages until implemented. |
| **Ignored Tariff Data** | HIGH | `standardize.py` does not ingest the `stdorToU` column from the raw CSV. | `backend/app/processing/standardize.py` | Tariff assignments should be propagated to calculate correct bills. | Column is completely dropped. | Add `tariff_type` mapping to standardization and schema. |
| **Synthetic Billing Data Missing** | HIGH | The project claims to combine real public data with simulated meter-to-cash entities, but billing logic is missing. | Billing Engine | System generates synthetic bills using real consumption * Tariff. | Bills only exist as hardcoded UI strings. | Implement a billing microservice to compute synthetic bills from the real consumption. |
| **Null Consumption Coercion** | MEDIUM | `fillna(0.0)` is used during numeric casting in `standardize.py`. | Data Quality / Standardization | Missing intervals should be preserved as `NULL` to detect meter communication failures. | Missing/bad intervals are silently cast to `0.0`. | Remove `fillna(0.0)` and rely on Data Quality Completeness rules instead. |
| **Partial Dataset Processing** | LOW | Dev testing only targets the first file (`targets = ["1"]`). | `smartmeter.py` CLI | The full 168-file ZIP should be processable. | Currently optimized only to process file `LCL-June2015v2_0.csv`. | Enable processing for all 168 chunks in production mode. |

**Important Note:** Do not manually fix these issues until the report has been fully reviewed.
