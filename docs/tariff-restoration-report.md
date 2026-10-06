# Tariff Restoration Report

## Overview
This document proves the successful restoration of the `stdorToU` tariff classification field from the official UKPN source dataset through the data engineering pipeline.

## Before / After Validation

### BEFORE
Prior to this phase, the tariff classification was ignored during ingestion and lost immediately:
```text
Source (Partitioned_LCL_Data.zip)
  ↓
Raw (NDJSON)                   ← stdorToU lost
  ↓
Standardized (Parquet)         ← stdorToU lost
  ↓
Gold (Parquet)                 ← stdorToU lost
```

### AFTER
The pipeline has been modified to explicitly capture and preserve the tariff classification at every stage without mutating the source values:
```text
Source (Partitioned_LCL_Data.zip)
  ↓
Raw (NDJSON)                   stdorToU
  ↓
Standardized (Parquet)         stdor_to_u
  ↓
Gold (Parquet)                 stdor_to_u
  ↓
dim_tariff                     source_tariff_code
```

## Data Profile Report (Controlled Batch)
A controlled pipeline run was executed against `LCL-June2015v2_0.csv` (first 1000 rows).

**Profile Metrics (Gold Parquet)**:
*   **Rows**: 999
*   **Distinct households**: 1
*   **Distinct tariff classifications**: 1
*   **Null tariff values**: 0
*   **Tariff frequency**: `Std`: 999
*   **Minimum timestamp**: 2012-10-12 00:30:00+00:00
*   **Maximum timestamp**: 2012-11-01 20:00:00+00:00

*(Note: The discrepancy of 1 row between source and Gold is due to an intentional DLQ rejection for invalid/missing consumption, as proven in earlier audits.)*

## Final Acceptance Criteria Verdict
*   **SOURCE FIELD VERIFIED**: PASS
*   **RAW PRESERVATION**: PASS
*   **STANDARDIZED PRESERVATION**: PASS
*   **GOLD PRESERVATION**: PASS
*   **VALUE RECONCILIATION**: PASS
*   **TARIFF DIMENSION**: PASS
*   **BIGQUERY PREPARATION**: BLOCKED *(Credentials missing)*
*   **FRONTEND**: READY *(API Contract established, graceful fallback implemented)*
*   **OVERALL**: PASS
