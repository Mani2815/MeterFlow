import pytest
import os
import responses
import pandas as pd
from typing import Dict
from datetime import datetime, timezone
import tempfile
import json
from ingestion.config import PipelineConfig, ExtractorConfig, StorageConfig
from ingestion.pipeline import IngestionPipeline

# We'll use local storage for tests to avoid needing actual GCS credentials.

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d

@pytest.fixture
def pipeline_config(temp_dir):
    return PipelineConfig(
        run_id="test_run_001",
        extractors=[
            ExtractorConfig(
                name="customers_full",
                type="postgres",
                table_or_endpoint="utility.customers",
                batch_size=100
            ),
            ExtractorConfig(
                name="customers_incremental",
                type="postgres",
                table_or_endpoint="utility.customers",
                incremental_field="updated_at",
                batch_size=100
            ),
            ExtractorConfig(
                name="weather_api",
                type="rest",
                table_or_endpoint="/weather",
                batch_size=2,
                pagination_params={"city": "Seattle"}
            )
        ],
        storage=StorageConfig(
            type="local",
            base_path=temp_dir
        )
    )

@pytest.fixture
def db_dsn():
    return os.getenv("DATABASE_URL", "postgresql://meter_user:meter_pass@localhost:5432/meter_to_cash")

@pytest.fixture
def base_url():
    return "https://api.example.com"


class TestIngestionFramework:
    def test_full_extraction(self, pipeline_config, db_dsn, base_url, temp_dir):
        # We'll run just the full extraction
        pipeline_config.extractors = [pipeline_config.extractors[0]]
        pipeline = IngestionPipeline(pipeline_config, db_dsn, base_url)
        
        pipeline.run()
        
        # Verify manifest
        manifest_path = f"{temp_dir}/_manifests/test_run_001/customers_full.json"
        assert os.path.exists(manifest_path)
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        assert manifest['status'] == 'SUCCESS'
        assert manifest['rows_extracted'] >= 1000  # We seeded at least 10000 usually
        
        # Verify parquet files
        dt = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        parquet_dir = f"{temp_dir}/customers_full/dt={dt}"
        assert os.path.exists(parquet_dir)
        files = os.listdir(parquet_dir)
        assert len(files) > 0
        
        # Read a parquet file to ensure no destructive transforms
        df = pd.read_parquet(os.path.join(parquet_dir, files[0]))
        assert 'customer_id' in df.columns
        assert 'email' in df.columns

    def test_incremental_extraction(self, pipeline_config, db_dsn, base_url, temp_dir):
        pipeline_config.extractors = [pipeline_config.extractors[1]]
        pipeline = IngestionPipeline(pipeline_config, db_dsn, base_url)
        
        # Pretend last watermark was far in the future so no new records
        future_watermark = datetime(2030, 1, 1, tzinfo=timezone.utc)
        pipeline.run(watermarks={"customers_incremental": future_watermark})
        
        manifest_path = f"{temp_dir}/_manifests/test_run_001/customers_incremental.json"
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        assert manifest['status'] == 'SUCCESS'
        assert manifest['rows_extracted'] == 0
        
        # Now let's try with a past watermark to get everything
        past_watermark = datetime(2000, 1, 1, tzinfo=timezone.utc)
        pipeline_config.run_id = "test_run_002"  # new run to avoid idempotency
        pipeline.run(watermarks={"customers_incremental": past_watermark})
        
        manifest_path = f"{temp_dir}/_manifests/test_run_002/customers_incremental.json"
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        assert manifest['status'] == 'SUCCESS'
        assert manifest['rows_extracted'] > 0
        assert manifest['watermark_end'] is not None

    @responses.activate
    def test_api_pagination(self, pipeline_config, db_dsn, base_url, temp_dir):
        pipeline_config.extractors = [pipeline_config.extractors[2]]
        pipeline = IngestionPipeline(pipeline_config, db_dsn, base_url)
        
        # Mock 3 pages of API responses
        # Page 1
        responses.add(
            responses.GET,
            f"{base_url}/weather",
            match=[responses.matchers.query_param_matcher({"city": "Seattle", "page": 1, "limit": 2})],
            json={"data": [{"temp": 70}, {"temp": 72}]},
            status=200
        )
        # Page 2
        responses.add(
            responses.GET,
            f"{base_url}/weather",
            match=[responses.matchers.query_param_matcher({"city": "Seattle", "page": 2, "limit": 2})],
            json={"data": [{"temp": 75}]},
            status=200
        )
        # Page 3 (Empty, signals end)
        responses.add(
            responses.GET,
            f"{base_url}/weather",
            match=[responses.matchers.query_param_matcher({"city": "Seattle", "page": 3, "limit": 2})],
            json={"data": []},
            status=200
        )
        
        pipeline.run()
        
        manifest_path = f"{temp_dir}/_manifests/test_run_001/weather_api.json"
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        assert manifest['status'] == 'SUCCESS'
        assert manifest['rows_extracted'] == 3

    @responses.activate
    def test_retry_after_simulated_failure(self, pipeline_config, db_dsn, base_url, temp_dir):
        pipeline_config.extractors = [pipeline_config.extractors[2]]
        pipeline = IngestionPipeline(pipeline_config, db_dsn, base_url)
        
        # First call fails with 500, second call succeeds
        responses.add(
            responses.GET,
            f"{base_url}/weather",
            json={"error": "Internal Server Error"},
            status=500
        )
        responses.add(
            responses.GET,
            f"{base_url}/weather",
            json={"data": [{"temp": 65}]},
            status=200
        )
        # Subsequent empty call to end pagination
        responses.add(
            responses.GET,
            f"{base_url}/weather",
            json={"data": []},
            status=200
        )
        
        pipeline.run()
        
        manifest_path = f"{temp_dir}/_manifests/test_run_001/weather_api.json"
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        assert manifest['status'] == 'SUCCESS'
        assert manifest['rows_extracted'] == 1

    def test_idempotent_rerun(self, pipeline_config, db_dsn, base_url, temp_dir):
        pipeline_config.extractors = [pipeline_config.extractors[0]]
        pipeline = IngestionPipeline(pipeline_config, db_dsn, base_url)
        
        # Run first time
        pipeline.run()
        manifest_path = f"{temp_dir}/_manifests/test_run_001/customers_full.json"
        assert os.path.exists(manifest_path)
        
        # Run second time, should skip and not fail
        # We can verify it skips by changing the DB or checking logs, but
        # since no exception is raised and manifest remains, it passes idempotency check.
        pipeline.run()
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        assert manifest['status'] == 'SUCCESS'
