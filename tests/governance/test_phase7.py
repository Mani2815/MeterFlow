import pytest
import os
import shutil
from governance.schema_registry import SchemaRegistry, IncompatibleSchemaError
from governance.backfill_manager import BackfillConfig, BackfillManager

@pytest.fixture
def clean_manifests():
    manifest_dir = "data/raw/_manifests"
    if os.path.exists(manifest_dir):
        shutil.rmtree(manifest_dir)
    yield
    if os.path.exists(manifest_dir):
        shutil.rmtree(manifest_dir)

def test_1_add_nullable_field():
    registry = SchemaRegistry()
    
    # Initial Schema
    v1_fields = {"customer_id": "str", "name": "str"}
    registry.detect_evolution("customers", v1_fields)
    assert registry.get_latest_schema("customers")["version"] == "1.0"
    
    # Evolve: Add nullable field 'email'
    v2_fields = {"customer_id": "str", "name": "str", "email": "str"}
    evolved = registry.detect_evolution("customers", v2_fields)
    
    assert evolved is True
    assert registry.get_latest_schema("customers")["version"] == "1.1"

def test_2_process_old_records():
    registry = SchemaRegistry()
    registry.register_schema("customers", {"customer_id": "str", "name": "str", "email": "str"}, version="1.1")
    
    # Payload from an old system without the 'email' field
    old_payload = {"customer_id": "CUST-01", "name": "Alice"}
    
    # Should not raise exception
    registry.validate_payload("customers", old_payload)

def test_3_process_new_records():
    registry = SchemaRegistry()
    registry.register_schema("customers", {"customer_id": "str", "name": "str", "email": "str"}, version="1.1")
    
    # Payload matching new schema
    new_payload = {"customer_id": "CUST-02", "name": "Bob", "email": "bob@example.com"}
    
    # Should not raise exception
    registry.validate_payload("customers", new_payload)

def test_4_perform_historical_backfill(clean_manifests):
    manager = BackfillManager()
    config = BackfillConfig(
        run_id="bf_2026_retro",
        table="meter_readings",
        start_date="2020-01-01",
        end_date="2020-12-31"
    )
    
    def dummy_generator(start, end):
        yield {"reading_id": "r1", "value": 100}
        yield {"reading_id": "r2", "value": 150}

    result = manager.execute_backfill(config, dummy_generator)
    
    assert result["status"] == "SUCCESS"
    assert result["records_processed"] == 2
    assert manager.is_already_processed("bf_2026_retro", "meter_readings") is True

def test_5_rerun_same_backfill(clean_manifests):
    manager = BackfillManager()
    config = BackfillConfig(
        run_id="bf_2026_retro",
        table="meter_readings",
        start_date="2020-01-01",
        end_date="2020-12-31"
    )
    
    def dummy_generator(start, end):
        yield {"reading_id": "r1"}

    # Run first time
    manager.execute_backfill(config, dummy_generator)
    
    # Rerun - should be idempotent
    result = manager.execute_backfill(config, dummy_generator)
    assert result["status"] == "SKIPPED"
    assert result["reason"] == "Already processed successfully."

def test_6_simulate_incompatible_type_change():
    registry = SchemaRegistry()
    v1_fields = {"customer_id": "str", "age": "int"}
    registry.detect_evolution("customers", v1_fields)
    
    # Simulate someone altering the source DB so 'age' is now a string
    v2_fields = {"customer_id": "str", "age": "str"}
    
    with pytest.raises(IncompatibleSchemaError) as excinfo:
        registry.detect_evolution("customers", v2_fields)
        
    assert "changed type from int to str" in str(excinfo.value)
    
    # Simulate someone dropping the 'customer_id' column
    v3_fields = {"age": "int"}
    with pytest.raises(IncompatibleSchemaError) as excinfo:
        registry.detect_evolution("customers", v3_fields)
        
    assert "was removed. This is a breaking change." in str(excinfo.value)
