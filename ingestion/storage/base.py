from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BaseStorage(ABC):
    @abstractmethod
    def write_parquet(self, path: str, df: pd.DataFrame) -> None:
        pass
        
    @abstractmethod
    def write_json(self, path: str, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def object_exists(self, path: str) -> bool:
        pass
