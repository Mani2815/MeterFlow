from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ExtractorConfig(BaseModel):
    name: str
    type: str # 'postgres' or 'rest'
    table_or_endpoint: str
    incremental_field: Optional[str] = None
    batch_size: int = 10000
    primary_key: Optional[str] = None
    # For REST
    headers: Dict[str, str] = Field(default_factory=dict)
    pagination_params: Dict[str, str] = Field(default_factory=dict)

class StorageConfig(BaseModel):
    type: str # 'gcs' or 'local'
    bucket: Optional[str] = None
    base_path: str = "data/raw"

class PipelineConfig(BaseModel):
    extractors: List[ExtractorConfig]
    storage: StorageConfig
    run_id: str
