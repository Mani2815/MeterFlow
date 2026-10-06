import psycopg2
import psycopg2.extras
from typing import Iterator, Dict, Any, List
from .base import BaseExtractor
from ingestion.config import ExtractorConfig

class PostgresExtractor(BaseExtractor):
    def __init__(self, config: ExtractorConfig, dsn: str):
        super().__init__(config)
        self.dsn = dsn

    def extract(self, watermark: Any = None) -> Iterator[List[Dict[str, Any]]]:
        conn = psycopg2.connect(self.dsn)
        conn.autocommit = True
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = f"SELECT * FROM {self.config.table_or_endpoint}"
                params = []
                if self.config.incremental_field and watermark:
                    query += f" WHERE {self.config.incremental_field} > %s"
                    params.append(watermark)
                if self.config.incremental_field:
                    query += f" ORDER BY {self.config.incremental_field} ASC"
                elif self.config.primary_key:
                    query += f" ORDER BY {self.config.primary_key} ASC"

                cur.execute(query, tuple(params))
                while True:
                    rows = cur.fetchmany(self.config.batch_size)
                    if not rows:
                        break
                    yield [dict(r) for r in rows]
        finally:
            conn.close()
