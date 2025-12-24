"""
API connector for JSON APIs
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.db.models.source import SourceConfig
from .base import BaseConnector


class APIConnector(BaseConnector):
    """Connector for JSON APIs"""
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.timeout = settings.ingestion_timeout_seconds
        self.user_agent = settings.ingestion_user_agent
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _fetch_api(self, url: str, headers: Dict = None, params: Dict = None) -> Any:
        """Fetch JSON from API with retries"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            request_headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json',
            }
            if headers:
                request_headers.update(headers)
            
            response = await client.get(
                url,
                headers=request_headers,
                params=params,
                follow_redirects=True
            )
            response.raise_for_status()
            return response.json()
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dict using dot notation"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            elif isinstance(value, list) and key.isdigit():
                value = value[int(key)]
            else:
                return None
        return value
    
    def _apply_mapping(self, item: Dict, mapping: Dict) -> Dict:
        """Apply field mapping to item"""
        result = {}
        for target_field, source_path in mapping.items():
            value = self._get_nested_value(item, source_path)
            if value is not None:
                result[target_field] = value
        return result
    
    def _generate_item_id(self, item: Dict) -> str:
        """Generate unique ID for API item"""
        # Try common ID fields
        for field in ['id', 'uid', 'uuid', 'reference', 'url', 'link']:
            if field in item and item[field]:
                return hashlib.sha256(str(item[field]).encode()).hexdigest()[:32]
        
        # Fallback to title
        title = item.get('title', item.get('name', str(item)))
        return hashlib.sha256(str(title).encode()).hexdigest()[:32]
    
    async def fetch(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch items from API"""
        items = []
        
        if not self.config.url:
            self.log_error("No URL configured for API source")
            return items
        
        try:
            # Prepare request
            headers = self.config.api_headers or {}
            params = dict(self.config.api_params or {})
            
            if limit:
                params['limit'] = limit
            
            # Fetch data
            data = await self._fetch_api(self.config.url, headers, params)
            
            # Handle different response formats
            if isinstance(data, list):
                raw_items = data
            elif isinstance(data, dict):
                # Try common list fields
                for field in ['data', 'items', 'results', 'records', 'entries']:
                    if field in data and isinstance(data[field], list):
                        raw_items = data[field]
                        break
                else:
                    raw_items = [data]  # Single item response
            else:
                self.log_error(f"Unexpected response type: {type(data)}")
                return items
            
            if limit:
                raw_items = raw_items[:limit]
            
            # Apply mapping if configured
            mapping = self.config.api_response_mapping or {}
            
            for raw_item in raw_items:
                try:
                    if mapping:
                        item = self._apply_mapping(raw_item, mapping)
                    else:
                        item = raw_item
                    
                    item_id = self._generate_item_id(raw_item)
                    
                    # Extract standard fields
                    title = item.get('title', item.get('name', 'Sans titre'))
                    content = item.get('description', item.get('content', item.get('body', '')))
                    link = item.get('url', item.get('link', item.get('href', '')))
                    
                    # Parse date if present
                    published_at = None
                    for date_field in ['published_at', 'created_at', 'date', 'publication_date']:
                        if date_field in item and item[date_field]:
                            try:
                                from dateutil import parser
                                published_at = parser.parse(item[date_field])
                                break
                            except:
                                pass
                    
                    items.append({
                        'item_id': item_id,
                        'title': title,
                        'content': content,
                        'links': [link] if link else [],
                        'primary_link': link,
                        'published_at': published_at,
                        'organization': item.get('organization', item.get('organisme', '')),
                        'location': item.get('location', item.get('lieu', '')),
                        'budget_text': item.get('budget', item.get('montant', '')),
                        'deadline_text': item.get('deadline', item.get('date_limite', '')),
                        'source_type': 'API',
                        'raw_data': raw_item,
                    })
                    
                except Exception as e:
                    self.log_error(f"Error parsing item: {str(e)}")
                    continue
                    
        except Exception as e:
            self.log_error(f"Error fetching API: {str(e)}")
        
        return items
    
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            headers = self.config.api_headers or {}
            params = self.config.api_params or {}
            
            data = await self._fetch_api(self.config.url, headers, params)
            return data is not None
            
        except Exception as e:
            self.log_error(f"Connection test failed: {str(e)}")
            return False
