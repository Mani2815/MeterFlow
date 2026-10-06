from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Pipeline(Base):
    __tablename__ = "pipeline"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    source = Column(String)
    destination = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PipelineRun(Base):
    __tablename__ = "pipeline_run"
    run_id = Column(String, primary_key=True)
    pipeline_id = Column(String, ForeignKey("pipeline.id"))
    status = Column(String, nullable=False) # STARTED, SUCCESS, FAILED
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    records_received = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    trigger_type = Column(String, nullable=False) # MANUAL, SCHEDULED, EVENT

class DLQEvent(Base):
    __tablename__ = "dlq_event"
    event_id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    dataset = Column(String, nullable=False)
    error_type = Column(String, nullable=False)
    error_message = Column(String, nullable=False)
    payload_reference = Column(String, nullable=False) # GCS URI or JSON
    attempt_count = Column(Integer, default=1)
    status = Column(String, default="PENDING") # PENDING, PROCESSING, RESOLVED, FAILED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class BackfillJob(Base):
    __tablename__ = "backfill_job"
    backfill_id = Column(String, primary_key=True)
    dataset = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="PENDING") # PENDING, RUNNING, SUCCESS, FAILED
    progress_pct = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

class DataQualityRun(Base):
    __tablename__ = "data_quality_run"
    id = Column(String, primary_key=True)
    run_id = Column(String, nullable=False) # Reference to standardize_run
    dataset = Column(String, nullable=False)
    overall_score = Column(Float, nullable=False)
    completeness = Column(Float, nullable=False)
    validity = Column(Float, nullable=False)
    uniqueness = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IngestionRun(Base):
    __tablename__ = "ingestion_run"
    run_id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    dataset = Column(String, nullable=False)
    source_file = Column(String, nullable=False)
    status = Column(String, nullable=False) # RUNNING, SUCCESS, FAILED
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    rows_received = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)
    checksum = Column(String, nullable=True)
    error_message = Column(String, nullable=True)

class StandardizeRun(Base):
    __tablename__ = "standardize_run"
    run_id = Column(String, primary_key=True)
    ingestion_run_id = Column(String, ForeignKey("ingestion_run.run_id"))
    dataset = Column(String, nullable=False)
    source_file = Column(String, nullable=False)
    status = Column(String, nullable=False) # RUNNING, SUCCESS, FAILED
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    rows_processed = Column(Integer, default=0)
    bytes_processed = Column(Integer, default=0)
    output_file = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
