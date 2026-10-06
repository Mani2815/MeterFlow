import pytest
import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that
from dataflow.transforms import ParseAndNormalizeCDC
import os

def test_parse_and_normalize_valid_cdc():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'datastream_sample_valid.json')
    with open(fixture_path, 'r') as f:
        valid_payload = f.read()

    with TestPipeline() as p:
        parsed = (
            p 
            | beam.Create([valid_payload])
            | beam.ParDo(ParseAndNormalizeCDC()).with_outputs(
                ParseAndNormalizeCDC.VALID_OUTPUT, 
                ParseAndNormalizeCDC.INVALID_OUTPUT
            )
        )
        
        valid = parsed[ParseAndNormalizeCDC.VALID_OUTPUT] | beam.Map(lambda x: x.to_dict())
        
        def check_result(actual):
            assert len(actual) == 1
            assert actual[0]['source_primary_key'] == "c200c821-1234"
            assert actual[0]['source_table'] == "customers"
            assert actual[0]['operation'] == "INSERT"
            assert "ACTIVE" in actual[0]['payload']
            assert "John" in actual[0]['payload']
            
        assert_that(valid, check_result)

def test_parse_and_normalize_invalid_cdc():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'datastream_sample_invalid.json')
    with open(fixture_path, 'r') as f:
        invalid_payload = f.read()

    with TestPipeline() as p:
        parsed = (
            p 
            | beam.Create([invalid_payload])
            | beam.ParDo(ParseAndNormalizeCDC()).with_outputs(
                ParseAndNormalizeCDC.VALID_OUTPUT, 
                ParseAndNormalizeCDC.INVALID_OUTPUT
            )
        )
        
        invalid = parsed[ParseAndNormalizeCDC.INVALID_OUTPUT]
        
        def check_error(actual):
            assert len(actual) == 1
            assert "error" in actual[0]
            assert "Missing required _metadata fields" in actual[0]["error"]
            
        assert_that(invalid, check_error)
