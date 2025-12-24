"""
Spotify Web API Provider
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from .base import BaseProvider

logger = logging.getLogger(__name__)


class SpotifyProvider(BaseProvider):
    """
    Fetches artist data from Spotify Web API
    - Genres
    - Followers
    - Popularity
    - Albums (for label fallback)
    """
    
    def __init__(self, config, spotify_client_id: str, spotify_client_secret: str, cache_client=None):
        super().__init__(config, cache_client)
        
        if not spotify_client_id or not spotify_client_secret:
            logger.warning("Spotify credentials not configured")
            self.client = None
        else:
            auth_manager = SpotifyClientCredentials(
                client_id=spotify_client_id,
                client_secret=spotify_client_secret
            )
            self.client = spotipy.Spotify(
                auth_manager=auth_manager,
                requests_timeout=config.timeout_spotify
            )
    
    async def fetch(self, artist_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch artist data from Spotify"""
        if not self.client:
            return None
        
        try:
            artist = self.client.artist(artist_id)
            
            return {
                "genres": artist.get("genres", []),
                "followers_total": artist.get("followers", {}).get("total"),
                "popularity": artist.get("popularity")
            }
            
        except Exception as e:
            logger.error(f"Spotify API error for {artist_id}: {e}")
            raise
    
    async def fetch_albums(self, artist_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch artist albums for label extraction"""
        if not self.client:
            return []
        
        try:
            albums = []
            results = self.client.artist_albums(
                artist_id,
                album_type="album,single",
                limit=50,
                country="FR"
            )
            
            albums.extend(results["items"])
            
            # Paginate if needed
            while results["next"] and len(albums) < limit:
                results = self.client.next(results)
                if results and "items" in results:
                    albums.extend(results["items"])
            
            # Get full album details (for label)
            detailed_albums = []
            for album in albums[:limit]:
                try:
                    full_album = self.client.album(album["id"])
                    detailed_albums.append(full_album)
                except Exception as e:
                    logger.warning(f"Could not fetch album {album['id']}: {e}")
            
            return detailed_albums
            
        except Exception as e:
            logger.error(f"Error fetching albums for {artist_id}: {e}")
            return []
