import pytest
from quality.validators import DataValidator
from quality.dlq import route_to_dlq
from quality.metrics import BatchQualityMetrics

def test_missing_required_field():
    v = DataValidator()
    payload = {"status": "ACTIVE"}
    errors = v.validate_record("customers", payload)
    assert len(errors) > 0
    assert "Missing primary key" in errors[0]

def test_negative_quantity_not_allowed():
    v = DataValidator()
    payload = {"meter_reading_id": "123", "reading_value": -50.0, "read_at": "2026-01-01"}
    errors = v.validate_record("meter_readings", payload)
    assert "Negative reading_value not allowed" in errors
    
def test_impossible_meter_reading():
    v = DataValidator()
    payload = {"meter_reading_id": "123", "reading_value": 10000000.0, "read_at": "2026-01-01"}
    errors = v.validate_record("meter_readings", payload)
    assert "reading_value exceeds realistic maximum" in errors

def test_financial_amount_negative():
    v = DataValidator()
    payload = {"bill_id": "123", "total_amount": -100.0}
    errors = v.validate_record("bills", payload)
    assert "Financial amount cannot be negative" in errors

def test_dlq_routing():
    v = DataValidator()
    payload = {"bill_id": "123", "total_amount": -100.0}
    errors = v.validate_record("bills", payload)
    
    dlq_record = route_to_dlq("datastream", "bills", payload, errors)
    assert dlq_record.error_category == "VALIDATION_ERROR"
    assert "Financial amount cannot be negative" in dlq_record.error_message
    assert '"total_amount": -100.0' in dlq_record.original_payload
    assert dlq_record.status == "UNRESOLVED"
    assert dlq_record.processing_attempt_count == 1

def test_batch_metrics():
    metrics = BatchQualityMetrics(run_id="batch_002", pipeline_name="ingest_billing", source="postgres")
    metrics.records_received = 100
    metrics.records_rejected = 2
    metrics.records_processed = 98
    metrics.validation_failures = 2
    metrics.finalize(exec_time=45, success=True)
    
    d = metrics.to_dict()
    assert d["status"] == "SUCCESS"
    assert d["records_rejected"] == 2
