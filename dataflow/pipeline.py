import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from .transforms import ParsePubSubNotification, ReadGCSFile, ParseAndNormalizeCDC

def build_pipeline(options: PipelineOptions, input_subscription: str, bq_table: str, bq_error_table: str):
    p = beam.Pipeline(options=options)
    
    notifications = (
        p 
        | "ReadNotifications" >> beam.io.ReadFromPubSub(subscription=input_subscription)
        | "ParseNotification" >> beam.ParDo(ParsePubSubNotification())
    )
    
    raw_lines = (
        notifications 
        | "ReadGCSFiles" >> beam.ParDo(ReadGCSFile())
    )
    
    parsed = (
        raw_lines 
        | "NormalizeCDC" >> beam.ParDo(ParseAndNormalizeCDC()).with_outputs(
            ParseAndNormalizeCDC.VALID_OUTPUT, 
            ParseAndNormalizeCDC.INVALID_OUTPUT
        )
    )
    
    valid_events = parsed[ParseAndNormalizeCDC.VALID_OUTPUT]
    invalid_events = parsed[ParseAndNormalizeCDC.INVALID_OUTPUT]
    
    deduplicated = (
        valid_events
        | "KeyByPK" >> beam.Map(lambda e: (f"{e.source_table}:{e.source_primary_key}:{e.operation}", e))
        # Windowing into FixedWindows would be needed for true streaming, omitted here for brevity
        | "GroupByKey" >> beam.GroupByKey()
        | "TakeLatest" >> beam.Map(lambda kv: sorted(kv[1], key=lambda x: x.ingestion_timestamp)[-1])
    )
    
    bq_schema = {
        'fields': [
            {'name': 'source_system', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'source_table', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'operation', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'source_primary_key', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'event_timestamp', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
            {'name': 'ingestion_timestamp', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
            {'name': 'schema_version', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'payload', 'type': 'JSON', 'mode': 'REQUIRED'},
        ]
    }
    
    deduplicated | "FormatToDict" >> beam.Map(lambda e: e.to_dict())                  | "WriteToBQ" >> beam.io.WriteToBigQuery(
                     table=bq_table,
                     schema=bq_schema,
                     write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                     create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
                 )
                 
    error_schema = {
        'fields': [
            {'name': 'error', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'raw', 'type': 'STRING', 'mode': 'NULLABLE'}
        ]
    }
    
    invalid_events | "WriteErrorsToBQ" >> beam.io.WriteToBigQuery(
                     table=bq_error_table,
                     schema=error_schema,
                     write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                     create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
                 )
                 
    return p
