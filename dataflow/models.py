from dataclasses import dataclass

@dataclass
class CanonicalEvent:
    source_system: str
    source_table: str
    operation: str
    source_primary_key: str
    event_timestamp: str
    ingestion_timestamp: str
    schema_version: str
    payload: str

    def to_dict(self):
        return {
            "source_system": self.source_system,
            "source_table": self.source_table,
            "operation": self.operation,
            "source_primary_key": self.source_primary_key,
            "event_timestamp": self.event_timestamp,
            "ingestion_timestamp": self.ingestion_timestamp,
            "schema_version": self.schema_version,
            "payload": self.payload
        }
