import apache_beam as beam
from apache_beam.metrics import Metrics
import json
import logging
from datetime import datetime, timezone
from .models import CanonicalEvent
from google.cloud import storage

class ParsePubSubNotification(beam.DoFn):
    def __init__(self):
        self.received_counter = Metrics.counter(self.__class__, 'received_notifications')
        
    def process(self, element: bytes):
        self.received_counter.inc()
        try:
            msg = json.loads(element.decode('utf-8'))
            bucket = msg.get("bucket")
            name = msg.get("name")
            if bucket and name:
                yield f"gs://{bucket}/{name}"
        except Exception as e:
            logging.error(f"Failed to parse notification: {e}")

class ReadGCSFile(beam.DoFn):
    def __init__(self):
        self.read_counter = Metrics.counter(self.__class__, 'files_read')
        self.error_counter = Metrics.counter(self.__class__, 'file_read_errors')

    def setup(self):
        self.client = storage.Client()

    def process(self, file_path: str):
        try:
            path_parts = file_path.replace("gs://", "").split("/")
            bucket_name = path_parts[0]
            blob_name = "/".join(path_parts[1:])
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            content = blob.download_as_string().decode('utf-8')
            
            for line in content.splitlines():
                if line.strip():
                    yield line
            self.read_counter.inc()
        except Exception as e:
            self.error_counter.inc()
            logging.error(f"Failed to read file {file_path}: {e}")

class ParseAndNormalizeCDC(beam.DoFn):
    VALID_OUTPUT = 'valid'
    INVALID_OUTPUT = 'invalid'
    
    def __init__(self):
        self.processed_counter = Metrics.counter(self.__class__, 'cdc_records_processed')
        self.invalid_counter = Metrics.counter(self.__class__, 'cdc_records_invalid')

    def process(self, element: str):
        self.processed_counter.inc()
        try:
            record = json.loads(element)
            meta = record.get("_metadata", {})
            
            table = meta.get("table")
            operation = meta.get("change_type")
            
            if not table or not operation:
                raise ValueError("Missing required _metadata fields (table or change_type)")
                
            pk = None
            if "customer_id" in record: pk = record["customer_id"]
            elif "account_id" in record: pk = record["account_id"]
            elif "meter_id" in record: pk = record["meter_id"]
            else:
                for k in record.keys():
                    if k != "_metadata":
                        pk = record[k]
                        break
                        
            if not pk:
                raise ValueError("Could not determine primary key from payload")
                
            event_timestamp = meta.get("timestamp", datetime.now(timezone.utc).isoformat())
            ingestion_timestamp = datetime.now(timezone.utc).isoformat()
            
            payload_data = {k: v for k, v in record.items() if k != "_metadata"}
            
            event = CanonicalEvent(
                source_system="datastream_postgres",
                source_table=table,
                operation=operation,
                source_primary_key=str(pk),
                event_timestamp=event_timestamp,
                ingestion_timestamp=ingestion_timestamp,
                schema_version="1.0",
                payload=json.dumps(payload_data)
            )
            yield beam.pvalue.TaggedOutput(self.VALID_OUTPUT, event)
            
        except Exception as e:
            self.invalid_counter.inc()
            yield beam.pvalue.TaggedOutput(self.INVALID_OUTPUT, {"error": str(e), "raw": element})
