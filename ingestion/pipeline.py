import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any
from ingestion.config import PipelineConfig, ExtractorConfig
from ingestion.extractors.postgres import PostgresExtractor
from ingestion.extractors.rest import RestExtractor
from ingestion.storage.gcs import GCSStorage
from ingestion.storage.local import LocalStorage
import logging

log = logging.getLogger(__name__)

class IngestionPipeline:
    def __init__(self, config: PipelineConfig, db_dsn: str, rest_base_url: str, storage_client=None):
        self.config = config
        self.db_dsn = db_dsn
        self.rest_base_url = rest_base_url
        
        if self.config.storage.type == 'gcs':
            self.storage = GCSStorage(self.config.storage.bucket, client=storage_client)
        else:
            self.storage = LocalStorage()

    def get_extractor(self, ext_conf: ExtractorConfig):
        if ext_conf.type == 'postgres':
            return PostgresExtractor(ext_conf, self.db_dsn)
        elif ext_conf.type == 'rest':
            return RestExtractor(ext_conf, self.rest_base_url)
        else:
            raise ValueError(f"Unknown extractor type: {ext_conf.type}")

    def check_idempotency(self, ext_name: str) -> bool:
        manifest_path = f"{self.config.storage.base_path}/_manifests/{self.config.run_id}/{ext_name}.json"
        return self.storage.object_exists(manifest_path)

    def run(self, watermarks: Dict[str, Any] = None):
        watermarks = watermarks or {}
        
        for ext_conf in self.config.extractors:
            log.info(f"Starting ingestion for {ext_conf.name}")
            
            if self.check_idempotency(ext_conf.name):
                log.info(f"Skipping {ext_conf.name}, already completed for run_id {self.config.run_id}")
                continue
                
            extractor = self.get_extractor(ext_conf)
            watermark = watermarks.get(ext_conf.name)
            
            total_rows = 0
            batch_num = 0
            max_watermark = watermark
            
            run_start = datetime.now(timezone.utc)
            status = "SUCCESS"
            error_msg = None
            
            try:
                for batch in extractor.extract(watermark):
                    if not batch:
                        continue
                    
                    df = pd.DataFrame(batch)
                    total_rows += len(df)
                    
                    # Compute new max watermark if applicable
                    if ext_conf.incremental_field:
                        batch_max = df[ext_conf.incremental_field].max()
                        if max_watermark is None or batch_max > max_watermark:
                            max_watermark = batch_max
                            
                    # Preserve original types, no destructive transformations
                    date_partition = run_start.strftime("%Y-%m-%d")
                    path = f"{self.config.storage.base_path}/{ext_conf.name}/dt={date_partition}/{self.config.run_id}_batch_{batch_num}.parquet"
                    
                    self.storage.write_parquet(path, df)
                    batch_num += 1
                
            except Exception as e:
                log.exception(f"Failed extracting {ext_conf.name}")
                status = "FAILED"
                error_msg = str(e)
                
            run_end = datetime.now(timezone.utc)
            
            # Write Manifest
            manifest = {
                "run_id": self.config.run_id,
                "dataset": ext_conf.name,
                "status": status,
                "start_time": run_start.isoformat(),
                "end_time": run_end.isoformat(),
                "rows_extracted": total_rows,
                "batches_written": batch_num,
                "watermark_start": str(watermark) if watermark else None,
                "watermark_end": str(max_watermark) if max_watermark else None,
                "error": error_msg
            }
            
            manifest_path = f"{self.config.storage.base_path}/_manifests/{self.config.run_id}/{ext_conf.name}.json"
            self.storage.write_json(manifest_path, manifest)
            
            if status == "FAILED":
                raise RuntimeError(f"Ingestion failed for {ext_conf.name}: {error_msg}")
