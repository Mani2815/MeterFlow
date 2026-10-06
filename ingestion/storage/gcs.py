import json
import pandas as pd
import tempfile
import os
from google.cloud import storage
from .base import BaseStorage
import logging

log = logging.getLogger(__name__)

class GCSStorage(BaseStorage):
    def __init__(self, bucket_name: str, client: storage.Client = None):
        self.client = client or storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def write_parquet(self, path: str, df: pd.DataFrame) -> None:
        blob = self.bucket.blob(path)
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
            df.to_parquet(tmp.name, engine='pyarrow', index=False)
            blob.upload_from_filename(tmp.name)
        os.remove(tmp.name)
        log.info(f"Uploaded parquet to gs://{self.bucket.name}/{path}")

    def write_json(self, path: str, data: dict) -> None:
        blob = self.bucket.blob(path)
        blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
        log.info(f"Uploaded JSON to gs://{self.bucket.name}/{path}")

    def object_exists(self, path: str) -> bool:
        blob = self.bucket.blob(path)
        return blob.exists()
