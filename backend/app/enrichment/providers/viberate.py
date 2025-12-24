"""
Viberate Web Scraping Provider
Fetches monthly listeners + social followers from Viberate.com
"""
import logging
import re
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from .base import BaseProvider

logger = logging.getLogger(__name__)


class ViberateProvider(BaseProvider):
    """
    Web scraping provider for Viberate.com
    
    Fetches:
    - Monthly listeners (Spotify)
    - Spotify followers
    - YouTube subscribers
    - Instagram followers
    - TikTok followers
    
    Note: Respecter les rate limits et les ToS de Viberate
    """
    
    BASE_URL = "https://www.viberate.com"
    SEARCH_URL = "https://www.viberate.com/search"
    
    # User-Agent rotation pour éviter les blocages
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    
    def __init__(self, config, cache_client=None):
        super().__init__(config, cache_client)
        self._user_agent_index = 0
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with current user agent"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.config.timeout_viberate,
                follow_redirects=True,
                headers=self._get_headers()
            )
        return self._http_client
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with rotating user agent"""
        ua = self.USER_AGENTS[self._user_agent_index % len(self.USER_AGENTS)]
        self._user_agent_index += 1
        
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
    
    async def _search_artist(self, artist_name: str) -> Optional[str]:
        """
        Search for artist on Viberate and return profile URL
        
        Args:
            artist_name: Name of the artist
            
        Returns:
            Viberate profile URL or None
        """
        client = await self._get_client()
        search_query = quote(artist_name)
        search_url = f"{self.SEARCH_URL}?q={search_query}"
        
        try:
            response = await client.get(search_url, headers=self._get_headers())
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher le premier résultat artiste
            # La structure peut varier, on cherche plusieurs patterns
            artist_links = soup.select('a[href*="/artist/"]')
            
            if artist_links:
                href = artist_links[0].get('href', '')
                if href.startswith('/'):
                    return f"{self.BASE_URL}{href}"
                return href
            
            # Alternative: chercher dans les résultats de recherche
            results = soup.select('.search-result-item, .artist-card, [data-artist-id]')
            for result in results:
                link = result.find('a', href=True)
                if link and '/artist/' in link['href']:
                    href = link['href']
                    if href.startswith('/'):
                        return f"{self.BASE_URL}{href}"
                    return href
            
            logger.warning(f"No artist found on Viberate for: {artist_name}")
            return None
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching Viberate: {e}")
            return None
        except Exception as e:
            logger.error(f"Error searching Viberate for {artist_name}: {e}")
            return None
    
    async def _search_artist_by_spotify_id(self, spotify_id: str) -> Optional[str]:
        """
        Try to find artist on Viberate using Spotify ID
        Viberate URLs often include the Spotify ID
        """
        # Viberate uses a specific URL pattern for Spotify-linked artists
        direct_url = f"{self.BASE_URL}/artist/{spotify_id}"
        
        try:
            client = await self._get_client()
            response = await client.get(direct_url, headers=self._get_headers())
            
            if response.status_code == 200:
                return direct_url
        except:
            pass
        
        return None
    
    def _parse_number(self, text: str) -> Optional[int]:
        """
        Parse numbers like '1.2M', '500K', '12,345' into integers
        """
        if not text:
            return None
        
        text = text.strip().upper().replace(',', '').replace(' ', '')
        
        multipliers = {
            'K': 1_000,
            'M': 1_000_000,
            'B': 1_000_000_000,
        }
        
        for suffix, multiplier in multipliers.items():
            if suffix in text:
                try:
                    number = float(text.replace(suffix, ''))
                    return int(number * multiplier)
                except ValueError:
                    continue
        
        # Try direct conversion
        try:
            return int(float(text))
        except ValueError:
            return None
    
    async def _scrape_artist_page(self, profile_url: str) -> Dict[str, Any]:
        """
        Scrape artist profile page for stats
        
        Returns dict with:
        - monthly_listeners
        - spotify_followers
        - youtube_subscribers
        - instagram_followers
        - tiktok_followers
        """
        client = await self._get_client()
        
        result = {
            "monthly_listeners": None,
            "spotify_followers": None,
            "youtube_subscribers": None,
            "instagram_followers": None,
            "tiktok_followers": None,
            "profile_url": profile_url,
            "scraped_at": datetime.now(),
        }
        
        try:
            # Add delay to avoid rate limiting
            await asyncio.sleep(self.config.viberate_request_delay)
            
            response = await client.get(profile_url, headers=self._get_headers())
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # === MONTHLY LISTENERS ===
            # Chercher dans différents patterns Viberate
            monthly_selectors = [
                '[data-stat="monthly-listeners"]',
                '.monthly-listeners',
                '.stat-monthly-listeners',
                'div:contains("Monthly Listeners")',
            ]
            
            for selector in monthly_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        # Chercher le nombre dans l'élément ou son voisin
                        text = element.get_text()
                        number = self._parse_number(text)
                        if number:
                            result["monthly_listeners"] = number
                            break
                except:
                    continue
            
            # Pattern alternatif: chercher texte "Monthly Listeners" puis nombre adjacent
            if not result["monthly_listeners"]:
                text = soup.get_text()
                match = re.search(r'Monthly\s*Listeners[:\s]*([0-9,.]+[KMB]?)', text, re.IGNORECASE)
                if match:
                    result["monthly_listeners"] = self._parse_number(match.group(1))
            
            # === SPOTIFY FOLLOWERS ===
            spotify_selectors = [
                '[data-platform="spotify"] .followers',
                '.spotify-followers',
                'a[href*="spotify.com"] + .stat',
                '[data-stat="spotify-followers"]',
            ]
            
            for selector in spotify_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        number = self._parse_number(element.get_text())
                        if number:
                            result["spotify_followers"] = number
                            break
                except:
                    continue
            
            if not result["spotify_followers"]:
                match = re.search(r'Spotify[:\s]*([0-9,.]+[KMB]?)\s*(?:followers?)?', text, re.IGNORECASE)
                if match:
                    result["spotify_followers"] = self._parse_number(match.group(1))
            
            # === YOUTUBE SUBSCRIBERS ===
            youtube_selectors = [
                '[data-platform="youtube"] .subscribers',
                '.youtube-subscribers',
                'a[href*="youtube.com"] + .stat',
                '[data-stat="youtube-subscribers"]',
            ]
            
            for selector in youtube_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        number = self._parse_number(element.get_text())
                        if number:
                            result["youtube_subscribers"] = number
                            break
                except:
                    continue
            
            if not result["youtube_subscribers"]:
                match = re.search(r'YouTube[:\s]*([0-9,.]+[KMB]?)\s*(?:subscribers?)?', text, re.IGNORECASE)
                if match:
                    result["youtube_subscribers"] = self._parse_number(match.group(1))
            
            # === INSTAGRAM FOLLOWERS ===
            instagram_selectors = [
                '[data-platform="instagram"] .followers',
                '.instagram-followers',
                'a[href*="instagram.com"] + .stat',
                '[data-stat="instagram-followers"]',
            ]
            
            for selector in instagram_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        number = self._parse_number(element.get_text())
                        if number:
                            result["instagram_followers"] = number
                            break
                except:
                    continue
            
            if not result["instagram_followers"]:
                match = re.search(r'Instagram[:\s]*([0-9,.]+[KMB]?)\s*(?:followers?)?', text, re.IGNORECASE)
                if match:
                    result["instagram_followers"] = self._parse_number(match.group(1))
            
            # === TIKTOK FOLLOWERS ===
            tiktok_selectors = [
                '[data-platform="tiktok"] .followers',
                '.tiktok-followers',
                'a[href*="tiktok.com"] + .stat',
                '[data-stat="tiktok-followers"]',
            ]
            
            for selector in tiktok_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        number = self._parse_number(element.get_text())
                        if number:
                            result["tiktok_followers"] = number
                            break
                except:
                    continue
            
            if not result["tiktok_followers"]:
                match = re.search(r'TikTok[:\s]*([0-9,.]+[KMB]?)\s*(?:followers?)?', text, re.IGNORECASE)
                if match:
                    result["tiktok_followers"] = self._parse_number(match.group(1))
            
            # Log results
            found_stats = [k for k, v in result.items() if v is not None and k not in ('profile_url', 'scraped_at')]
            logger.info(f"Viberate scrape: found {len(found_stats)} stats: {found_stats}")
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error scraping Viberate: {e}")
            raise
        except Exception as e:
            logger.error(f"Error scraping Viberate page {profile_url}: {e}")
            raise
    
    async def fetch(self, artist_input: str, artist_name: Optional[str] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch all social stats for an artist from Viberate
        
        Args:
            artist_input: Spotify artist ID or name
            artist_name: Optional artist name for search
            
        Returns:
            Dict with all social stats or None
        """
        profile_url = None
        
        # Try by Spotify ID first
        if re.match(r'^[a-zA-Z0-9]{22}$', artist_input):
            profile_url = await self._search_artist_by_spotify_id(artist_input)
        
        # If not found, search by name
        if not profile_url:
            search_name = artist_name or artist_input
            profile_url = await self._search_artist(search_name)
        
        if not profile_url:
            logger.warning(f"Could not find artist on Viberate: {artist_input}")
            return None
        
        try:
            stats = await self._scrape_artist_page(profile_url)
            
            return {
                "monthly_listeners": {
                    "value": stats.get("monthly_listeners"),
                    "provider": "viberate:scraping",
                    "retrieved_at": stats["scraped_at"],
                    "confidence": 0.95 if stats.get("monthly_listeners") else 0.0,
                    "evidence": [f"Scraped from {profile_url}"]
                },
                "social_stats": {
                    "spotify_followers": stats.get("spotify_followers"),
                    "youtube_subscribers": stats.get("youtube_subscribers"),
                    "instagram_followers": stats.get("instagram_followers"),
                    "tiktok_followers": stats.get("tiktok_followers"),
                    "provider": "viberate:scraping",
                    "retrieved_at": stats["scraped_at"],
                    "profile_url": profile_url
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch from Viberate: {e}")
            raise
    
    async def fetch_batch(self, artists: List[Dict[str, str]]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch stats for multiple artists
        
        Args:
            artists: List of dicts with 'id' (spotify_id) and optionally 'name'
            
        Returns:
            Dict mapping artist IDs to their stats
        """
        results = {}
        
        for artist in artists:
            artist_id = artist.get('id')
            artist_name = artist.get('name')
            
            try:
                result = await self.fetch(artist_id, artist_name)
                results[artist_id] = result
            except Exception as e:
                logger.error(f"Batch fetch failed for {artist_id}: {e}")
                results[artist_id] = None
            
            # Rate limiting between requests
            await asyncio.sleep(self.config.viberate_request_delay)
        
        return results
    
    async def close(self):
        """Close HTTP client"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
