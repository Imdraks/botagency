"""
HTML scraping connector
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.db.models.source import SourceConfig
from .base import BaseConnector


class HTMLConnector(BaseConnector):
    """Connector for HTML page scraping"""
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.timeout = settings.ingestion_timeout_seconds
        self.user_agent = settings.ingestion_user_agent
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _fetch_page(self, url: str) -> str:
        """Fetch HTML page with retries"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.text
    
    def _get_selector_text(self, element, selector: str) -> Optional[str]:
        """Get text from element using CSS selector"""
        if not selector:
            return None
        
        found = element.select_one(selector)
        if found:
            return found.get_text(strip=True)
        return None
    
    def _get_selector_attr(self, element, selector: str, attr: str = 'href') -> Optional[str]:
        """Get attribute from element using CSS selector"""
        if not selector:
            return None
        
        found = element.select_one(selector)
        if found and found.has_attr(attr):
            return found[attr]
        return None
    
    def _generate_item_id(self, url: str, title: str) -> str:
        """Generate unique ID for item"""
        if url:
            return hashlib.sha256(url.encode()).hexdigest()[:32]
        return hashlib.sha256(title.encode()).hexdigest()[:32]
    
    async def fetch(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch items from HTML page"""
        items = []
        
        if not self.config.url:
            self.log_error("No URL configured for HTML source")
            return items
        
        selectors = self.config.html_selectors or {}
        item_selector = selectors.get('item_selector')
        
        if not item_selector:
            self.log_error("No item_selector configured")
            return items
        
        try:
            html = await self._fetch_page(self.config.url)
            soup = BeautifulSoup(html, 'lxml')
            
            elements = soup.select(item_selector)
            
            if limit:
                elements = elements[:limit]
            
            for element in elements:
                try:
                    # Extract fields using selectors
                    title = self._get_selector_text(element, selectors.get('title_selector'))
                    if not title:
                        continue  # Skip items without title
                    
                    description = self._get_selector_text(element, selectors.get('description_selector'))
                    link = self._get_selector_attr(element, selectors.get('link_selector'), 'href')
                    deadline_text = self._get_selector_text(element, selectors.get('deadline_selector'))
                    organization = self._get_selector_text(element, selectors.get('organization_selector'))
                    location = self._get_selector_text(element, selectors.get('location_selector'))
                    budget_text = self._get_selector_text(element, selectors.get('budget_selector'))
                    
                    # Make link absolute
                    if link and not link.startswith(('http://', 'https://')):
                        link = urljoin(self.config.url, link)
                    
                    # Extract all links from the item
                    links = []
                    for a in element.select('a[href]'):
                        href = a['href']
                        if href.startswith(('http://', 'https://')):
                            links.append(href)
                        elif not href.startswith(('#', 'javascript:', 'mailto:')):
                            links.append(urljoin(self.config.url, href))
                    links = list(set(links))
                    
                    item_id = self._generate_item_id(link or "", title)
                    
                    items.append({
                        'item_id': item_id,
                        'title': title,
                        'content': description or "",
                        'links': links,
                        'primary_link': link,
                        'deadline_text': deadline_text,
                        'organization': organization,
                        'location': location,
                        'budget_text': budget_text,
                        'source_type': 'HTML',
                        'source_url': self.config.url,
                    })
                    
                except Exception as e:
                    self.log_error(f"Error parsing element: {str(e)}")
                    continue
            
            # Handle pagination if configured
            pagination_selector = selectors.get('pagination_selector')
            if pagination_selector and len(items) > 0:
                # For now, just log that pagination exists
                next_page = self._get_selector_attr(soup, pagination_selector, 'href')
                if next_page:
                    self.log_error(f"Pagination detected: {next_page} (not followed in V1)")
                    
        except Exception as e:
            self.log_error(f"Error fetching page: {str(e)}")
        
        return items
    
    async def test_connection(self) -> bool:
        """Test HTML scraping connection"""
        try:
            html = await self._fetch_page(self.config.url)
            soup = BeautifulSoup(html, 'lxml')
            
            selectors = self.config.html_selectors or {}
            item_selector = selectors.get('item_selector')
            
            if item_selector:
                elements = soup.select(item_selector)
                return len(elements) > 0
            
            return True  # Page fetched successfully
            
        except Exception as e:
            self.log_error(f"Connection test failed: {str(e)}")
            return False
