# Tariff Gap Analysis

## Overview
This document outlines the exact point where the `stdorToU` (Standard or Time of Use) tariff classification field is dropped in the data pipeline.

## The Break
The dataset lineage audit and source schema validation revealed that the official UK Power Networks dataset contains a column named `stdorToU`. However, it does not exist in the Gold dataset.

### Trace
1. **Source column**: `stdorToU` is present in the CSV file downloaded from the London Datastore.
2. **Parser**: The data is read via `csv.DictReader` in `backend/app/ingestion/smartmeter.py:process_csv_file`. Each row is passed to `validate_row(row)`.
3. **Drop Location**: Inside `validate_row`, the code extracts `LCLid` (household), `DateTime` (timestamp), and `KWH/hh (per half hour)` (consumption), but it explicitly ignores `row.get("stdorToU")`. 
4. **Raw representation**: The generated NDJSON written to `/tmp/mock_gcs/utility/raw/smartmeter/` only contains `meter_id`, `household_id`, `event_timestamp`, `consumption_kwh`, and `source_system`.
5. **Standardization**: `backend/app/processing/standardize.py` reads the Raw JSON. Since the tariff field is not in Raw, it is not passed to the canonical schema.
6. **Gold representation**: The Quality engine (`backend/app/processing/quality.py`) drops invalid rows, but again, the field is already gone, so Gold Parquet completely lacks the tariff classification.

## Conclusion
To preserve the tariff classification, `stdorToU` must be explicitly read in `validate_row` and passed through into the Raw NDJSON layer. Then, `standardize.py` must rename it to the canonical `stdor_to_u` and `quality.py` must propagate it to the Gold Parquet.
