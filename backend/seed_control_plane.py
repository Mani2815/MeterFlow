import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.core import Pipeline, PipelineRun, DLQEvent, BackfillJob, DataQualityRun
import datetime

async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession)
    
    async with session_factory() as db:
        # Seed Pipelines
        p1 = Pipeline(id="pipe_mtr_ingest_01", name="Meter Reading Ingestion", type="Batch", source="PostgreSQL", destination="BigQuery", is_active=True)
        p2 = Pipeline(id="pipe_bill_cdc_01", name="Billing CDC", type="Streaming", source="Datastream", destination="Pub/Sub", is_active=True)
        
        db.add_all([p1, p2])
        await db.flush()
        
        # Seed Runs
        r1 = PipelineRun(run_id="RUN-20261006-1042", pipeline_id="pipe_mtr_ingest_01", status="SUCCESS", records_received=12842, records_processed=12830, records_rejected=12, duration_ms=102000, trigger_type="SCHEDULED", completed_at=datetime.datetime.now(datetime.timezone.utc))
        
        db.add_all([r1])
        await db.flush()
        
        # Seed Quality
        q1 = DataQualityRun(id="qrun_01", run_id="RUN-20261006-1042", dataset="meter_readings", overall_score=99.7, completeness=99.9, validity=99.6, uniqueness=99.8)
        db.add_all([q1])
        await db.flush()
        
        # Seed DLQ
        d1 = DLQEvent(event_id="EVT-89231", source="PostgreSQL", dataset="bills", error_type="VALIDATION_ERROR", error_message="Negative payment amount", payload_reference="gs://dlq/evt-89231.json", status="PENDING")
        db.add_all([d1])
        
        await db.commit()
        print("Database seeded!")
        
if __name__ == "__main__":
    asyncio.run(seed())
