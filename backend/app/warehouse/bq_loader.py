import os
import argparse
import logging
from google.cloud import bigquery
import pandas as pd
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("warehouse.bq_loader")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

LOCAL_GCS_MOCK_DIR = os.getenv("STORAGE_DIR", "/tmp/mock_gcs")
PROJECT_ID = os.getenv("GCP_PROJECT", "meter-to-cash-project")
DATASET_ID = "utility_analytics"
TABLE_ID = "fact_meter_reading"

def load_gold_to_bq(standardize_run_id: str):
    logger.info("Starting BigQuery load", extra={"standardize_run_id": standardize_run_id})
    
    parquet_path = os.path.join(LOCAL_GCS_MOCK_DIR, f"utility/gold/smartmeter/gold_{standardize_run_id}.parquet")
    if not os.path.exists(parquet_path):
        logger.error("Gold parquet file not found", extra={"path": parquet_path})
        return
        
    df = pd.read_parquet(parquet_path)
    if df.empty:
        logger.warning("Empty dataframe, nothing to load")
        return
        
    # Rename columns to match the Fact table schema defined in docs
    df = df.rename(columns={
        "household_id": "source_household_id",
        "event_timestamp": "reading_timestamp",
        "processed_at": "ingestion_date"
    })
    
    # Ensure dataset exists
    try:
        client = bigquery.Client(project=PROJECT_ID)
        dataset_ref = client.dataset(DATASET_ID)
        
        try:
            client.get_dataset(dataset_ref)
        except Exception:
            # Create dataset if not found
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            client.create_dataset(dataset)
            
        table_ref = dataset_ref.table(TABLE_ID)
        
        job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("source_household_id", "STRING"),
                bigquery.SchemaField("meter_id", "STRING"),
                bigquery.SchemaField("reading_timestamp", "TIMESTAMP"),
                bigquery.SchemaField("consumption_kwh", "FLOAT64"),
                bigquery.SchemaField("stdor_to_u", "STRING"),
                bigquery.SchemaField("source_system", "STRING"),
                bigquery.SchemaField("ingestion_date", "TIMESTAMP"),
                bigquery.SchemaField("ingestion_run_id", "STRING"),
                bigquery.SchemaField("standardize_run_id", "STRING"),
            ],
            write_disposition="WRITE_APPEND",
            time_partitioning=bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="reading_timestamp"
            ),
            clustering_fields=["source_household_id"]
        )
        
        logger.info("Submitting BigQuery load job...")
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # Wait for the job to complete
        
        table = client.get_table(table_ref)
        logger.info("BigQuery load complete", extra={
            "rows_loaded": len(df),
            "total_table_rows": table.num_rows
        })
        
    except Exception as e:
        logger.error("Failed to load into BigQuery", extra={"error": str(e)})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--standardize-run-id", required=True)
    args = parser.parse_args()
    load_gold_to_bq(args.standardize_run_id)
