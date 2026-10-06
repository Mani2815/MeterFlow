from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, List
from ingestion.config import ExtractorConfig

class BaseExtractor(ABC):
    def __init__(self, config: ExtractorConfig):
        self.config = config

    @abstractmethod
    def extract(self, watermark: Any = None) -> Iterator[List[Dict[str, Any]]]:
        pass
