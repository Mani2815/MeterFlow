from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class BatchQualityMetrics:
    run_id: str
    pipeline_name: str
    source: str
    records_received: int = 0
    records_processed: int = 0
    records_rejected: int = 0
    duplicate_count: int = 0
    null_count: int = 0
    validation_failures: int = 0
    execution_time_seconds: int = 0
    status: str = "RUNNING"
    run_timestamp: str = ""
    
    def finalize(self, exec_time: int, success: bool):
        self.execution_time_seconds = exec_time
        self.status = "SUCCESS" if success else "FAILED"
        self.run_timestamp = datetime.now(timezone.utc).isoformat()
        
    def to_dict(self):
        return {
            "run_id": self.run_id,
            "pipeline_name": self.pipeline_name,
            "source": self.source,
            "records_received": self.records_received,
            "records_processed": self.records_processed,
            "records_rejected": self.records_rejected,
            "duplicate_count": self.duplicate_count,
            "null_count": self.null_count,
            "validation_failures": self.validation_failures,
            "execution_time_seconds": self.execution_time_seconds,
            "status": self.status,
            "run_timestamp": self.run_timestamp
        }
