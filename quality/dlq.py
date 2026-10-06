import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class DLQRecord:
    dlq_id: str
    source_system: str
    source_table: str
    original_payload: str
    error_category: str
    error_message: str
    processing_attempt_count: int
    failure_timestamp: str
    status: str = "UNRESOLVED"

def route_to_dlq(source_system: str, source_table: str, payload: Any, errors: list, attempt: int = 1) -> DLQRecord:
    payload_str = json.dumps(payload) if isinstance(payload, dict) else str(payload)
        
    return DLQRecord(
        dlq_id=str(uuid.uuid4()),
        source_system=source_system,
        source_table=source_table,
        original_payload=payload_str,
        error_category="VALIDATION_ERROR",
        error_message="; ".join(errors),
        processing_attempt_count=attempt,
        failure_timestamp=datetime.now(timezone.utc).isoformat()
    )
