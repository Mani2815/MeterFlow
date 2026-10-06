import json
import pandas as pd
import os
from .base import BaseStorage
import logging

log = logging.getLogger(__name__)

class LocalStorage(BaseStorage):
    def write_parquet(self, path: str, df: pd.DataFrame) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_parquet(path, engine='pyarrow', index=False)
        log.info(f"Wrote parquet to {path}")

    def write_json(self, path: str, data: dict) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        log.info(f"Wrote JSON to {path}")

    def object_exists(self, path: str) -> bool:
        return os.path.exists(path)
