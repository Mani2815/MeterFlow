import requests
from typing import Iterator, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .base import BaseExtractor
from ingestion.config import ExtractorConfig
import logging

log = logging.getLogger(__name__)

class RestExtractor(BaseExtractor):
    def __init__(self, config: ExtractorConfig, base_url: str):
        super().__init__(config)
        self.base_url = base_url

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def _fetch_page(self, url: str, params: Dict[str, Any]) -> requests.Response:
        log.info(f"Fetching {url} with params {params}")
        resp = requests.get(url, headers=self.config.headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp

    def extract(self, watermark: Any = None) -> Iterator[List[Dict[str, Any]]]:
        url = f"{self.base_url.rstrip('/')}/{self.config.table_or_endpoint.lstrip('/')}"
        page = 1
        limit = self.config.batch_size
        
        while True:
            params = dict(self.config.pagination_params)
            params['page'] = page
            params['limit'] = limit
            if self.config.incremental_field and watermark:
                params[f'{self.config.incremental_field}_gt'] = watermark
            
            resp = self._fetch_page(url, params)
            data = resp.json()
            
            items = data if isinstance(data, list) else data.get('data', [])
            if not items:
                break
                
            yield items
            
            if len(items) < limit:
                break
            page += 1
