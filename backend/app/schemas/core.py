from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class PipelineBase(BaseModel):
    name: str
    type: str
    source: Optional[str] = None
    destination: Optional[str] = None
    is_active: bool = True

class PipelineSchema(PipelineBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PipelineRunSchema(BaseModel):
    run_id: str
    pipeline_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_received: int
    records_processed: int
    records_rejected: int
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    trigger_type: str
    model_config = ConfigDict(from_attributes=True)

class PipelineRunRequest(BaseModel):
    trigger_type: str = "MANUAL"

class DLQEventSchema(BaseModel):
    event_id: str
    source: str
    dataset: str
    error_type: str
    error_message: str
    payload_reference: str
    attempt_count: int
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class BackfillRequest(BaseModel):
    dataset: str
    start_date: datetime
    end_date: datetime

class BackfillSchema(BaseModel):
    backfill_id: str
    dataset: str
    start_date: datetime
    end_date: datetime
    status: str
    progress_pct: int
    records_processed: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class QualitySummarySchema(BaseModel):
    overall_score: float
    completeness: float
    validity: float
    uniqueness: float
    consistency: float
    timeliness: float

class MetricSchema(BaseModel):
    label: str
    value: str
    color: Optional[str] = None
