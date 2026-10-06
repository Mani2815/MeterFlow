import os
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class BackfillConfig:
    run_id: str
    table: str
    start_date: str
    end_date: str
    is_backfill: bool = True

class BackfillManager:
    def __init__(self, manifest_dir: str = "data/raw/_manifests"):
        self.manifest_dir = manifest_dir
        os.makedirs(self.manifest_dir, exist_ok=True)

    def _get_manifest_path(self, run_id: str, table: str) -> str:
        run_dir = os.path.join(self.manifest_dir, run_id)
        os.makedirs(run_dir, exist_ok=True)
        return os.path.join(run_dir, f"{table}_backfill.json")

    def is_already_processed(self, run_id: str, table: str) -> bool:
        """Idempotency check"""
        path = self._get_manifest_path(run_id, table)
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                return data.get("status") == "SUCCESS"
        return False

    def execute_backfill(self, config: BackfillConfig, payload_generator) -> Dict[str, Any]:
        """
        Simulates extracting and processing records specifically for a backfill.
        Tags payloads heavily to distinguish from live CDC.
        """
        if self.is_already_processed(config.run_id, config.table):
            return {"status": "SKIPPED", "reason": "Already processed successfully."}

        records_processed = 0
        try:
            for record in payload_generator(config.start_date, config.end_date):
                # Tagging the record
                record["_metadata_run_id"] = config.run_id
                record["_metadata_is_backfill"] = True
                records_processed += 1
                
            status = "SUCCESS"
            error = None
        except Exception as e:
            status = "FAILED"
            error = str(e)
            
        manifest = {
            "run_id": config.run_id,
            "table": config.table,
            "start_date": config.start_date,
            "end_date": config.end_date,
            "records_processed": records_processed,
            "status": status,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with open(self._get_manifest_path(config.run_id, config.table), 'w') as f:
            json.dump(manifest, f)
            
        if status == "FAILED":
            raise RuntimeError(f"Backfill failed: {error}")
            
        return manifest
