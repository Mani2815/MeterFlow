import os
import logging
from ingestion.config import PipelineConfig, ExtractorConfig, StorageConfig
from ingestion.pipeline import IngestionPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    config = PipelineConfig(
        run_id="run_batch_001",
        extractors=[
            ExtractorConfig(
                name="customers_incremental",
                type="postgres",
                table_or_endpoint="utility.customers",
                incremental_field="updated_at",
                batch_size=5000
            )
        ],
        storage=StorageConfig(
            type="local",
            base_path="data/raw"
        )
    )
    
    db_dsn = os.getenv("DATABASE_URL", "postgresql://meter_user:meter_pass@localhost:5432/meter_to_cash")
    
    pipeline = IngestionPipeline(config, db_dsn, "https://api.example.com")
    pipeline.run()

if __name__ == "__main__":
    main()
