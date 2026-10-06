# UK Power Networks - SmartMeter Energy Consumption Data

## Overview
- **Dataset Name**: SmartMeter Energy Consumption Data in London Households
- **Publisher**: UK Power Networks (via London Datastore)
- **Source URL**: https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d
- **Licence**: Creative Commons Attribution (CC BY 4.0)
- **Timeframe**: November 2011 to February 2014

## Resources
The dataset is provided in two main formats, plus an additional tariff file:
1. **Full Dataset (LCL-FullData.zip)**: ~764 MB compressed, ~10 GB uncompressed CSV containing ~167 million rows.
2. **Partitioned Dataset (Partitioned LCL Data.zip)**: ~758 MB compressed. Contains the same 167 million rows split across 168 individual CSV files (approx 1 million rows each).
3. **Tariff Data (Tariffs.xlsx)**: ~240 KB. Contains Time of Use (dToU) tariffs for 2013.

### Download URLs
- **Partitioned Data (168 files)**: `https://data.london.gov.uk/download/vqm0d/04feba67-f1a3-4563-98d0-f3071e3d56d1/Partitioned%20LCL%20Data.zip`
- **Tariff Data**: `https://data.london.gov.uk/download/vqm0d/14855047-44c2-4856-8a48-e5649200e6ce/Tariffs.xlsx`

## Columns (Expected based on description)
- `LCLid` (Household identifier)
- `stdorToU` (Tariff type - Standard or Time of Use)
- `DateTime` (Date and time of the reading)
- `KWH/hh (per half hour)` (Energy consumption in kWh)

## Size and Partitioning
- **Total Rows**: ~167,000,000
- **Uncompressed Size**: ~10 GB
- **Partitioning**: The partitioned zip contains 168 CSV files. Each file contains roughly 1,000,000 rows.

## Ingestion Approach
- **Direct Internet Ingestion**: The ingestion service will download the partitioned ZIP file (or Tariffs.xlsx) directly over HTTPS.
- **Streaming/Chunking**: Due to the zip format requiring the Central Directory at the end of the file, the 758MB zip will be streamed to a local temporary file (with bounded memory usage). The ingestion service will then stream the uncompressed CSV data directly from the ZIP file into chunks, validating and uploading them to Google Cloud Storage (GCS) without ever loading the full 10GB uncompressed dataset into memory. 
- **Idempotency**: Ingestion will track downloaded zip files and individual CSVs inside the zip.
- **Normalization**: Household IDs (`LCLid`) will be mapped to a simulated `meter_id`. The dataset does not contain customer names or billing records; it contains household-level smart-meter consumption information.

## Limitations
- **Historical Data**: This is a historical dataset (2011-2014), not a live feed.
- **Household Identifiers**: Contains `LCLid` (household IDs), which we will simulate as meter IDs.
- **Tariff Coverage**: Only covers the dToU tariff structure for 2013 for a subset of customers; remaining customers use a flat rate.

## Attribution Requirements
Must attribute UK Power Networks and London Datastore as the source of the raw data, and clearly state that downstream enterprise entities (customers, accounts, billing) are synthetic/simulated.
