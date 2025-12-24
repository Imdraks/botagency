"""
RSS/Atom feed connector
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

import feedparser
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.db.models.source import SourceConfig
from .base import BaseConnector


class RSSConnector(BaseConnector):
    """Connector for RSS/Atom feeds"""
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.timeout = settings.ingestion_timeout_seconds
        self.user_agent = settings.ingestion_user_agent
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _fetch_feed(self, url: str) -> feedparser.FeedParserDict:
        """Fetch and parse RSS feed with retries"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {'User-Agent': self.user_agent}
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            return feedparser.parse(response.text)
    
    def _parse_date(self, entry: Dict) -> Optional[datetime]:
        """Parse publication date from feed entry"""
        for date_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if date_field in entry and entry[date_field]:
                try:
                    import time
                    return datetime.fromtimestamp(time.mktime(entry[date_field]))
                except:
                    pass
        
        # Try string parsing
        for date_field in ['published', 'updated', 'created']:
            if date_field in entry and entry[date_field]:
                try:
                    from dateutil import parser
                    return parser.parse(entry[date_field])
                except:
                    pass
        
        return None
    
    def _get_entry_id(self, entry: Dict) -> str:
        """Generate unique ID for entry"""
        # Use entry id if available
        if entry.get('id'):
            return hashlib.sha256(entry['id'].encode()).hexdigest()[:32]
        
        # Fallback to link
        if entry.get('link'):
            return hashlib.sha256(entry['link'].encode()).hexdigest()[:32]
        
        # Fallback to title + date
        title = entry.get('title', '')
        date = str(entry.get('published', ''))
        return hashlib.sha256(f"{title}{date}".encode()).hexdigest()[:32]
    
    def _extract_content(self, entry: Dict) -> str:
        """Extract content from entry"""
        # Try content first
        if 'content' in entry and entry['content']:
            content = entry['content'][0].get('value', '')
            if content:
                return content
        
        # Try summary
        if entry.get('summary'):
            return entry['summary']
        
        # Try description
        if entry.get('description'):
            return entry['description']
        
        return ""
    
    async def fetch(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch items from RSS feed"""
        items = []
        
        if not self.config.url:
            self.log_error("No URL configured for RSS source")
            return items
        
        try:
            feed = await self._fetch_feed(self.config.url)
            
            if feed.bozo and feed.bozo_exception:
                self.log_error(f"Feed parsing warning: {str(feed.bozo_exception)}")
            
            entries = feed.entries
            if limit:
                entries = entries[:limit]
            
            for entry in entries:
                try:
                    entry_id = self._get_entry_id(entry)
                    title = entry.get('title', 'Sans titre')
                    link = entry.get('link', '')
                    content = self._extract_content(entry)
                    published_at = self._parse_date(entry)
                    
                    # Extract all links
                    links = [link] if link else []
                    if 'links' in entry:
                        for l in entry['links']:
                            if l.get('href'):
                                links.append(l['href'])
                    links = list(set(links))
                    
                    # Author/organization
                    author = entry.get('author', '')
                    if not author and 'authors' in entry and entry['authors']:
                        author = entry['authors'][0].get('name', '')
                    
                    items.append({
                        'entry_id': entry_id,
                        'title': title,
                        'content': content,
                        'links': links,
                        'primary_link': link,
                        'published_at': published_at,
                        'author': author,
                        'source_type': 'RSS',
                        'feed_title': feed.feed.get('title', ''),
                    })
                    
                except Exception as e:
                    self.log_error(f"Error parsing entry: {str(e)}")
                    continue
                    
        except Exception as e:
            self.log_error(f"Error fetching feed: {str(e)}")
        
        return items
    
    async def test_connection(self) -> bool:
        """Test RSS feed connection"""
        try:
            feed = await self._fetch_feed(self.config.url)
            return len(feed.entries) >= 0  # Success even if empty
        except Exception as e:
            self.log_error(f"Connection test failed: {str(e)}")
            return False
