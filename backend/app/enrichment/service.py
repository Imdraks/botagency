"""
Artist Enrichment Service
Orchestrates all providers - Uses Viberate for web scraping
"""
import logging
import re
from typing import Optional, List
from datetime import datetime

from .config import EnrichmentConfig
from .models import (
    EnrichedArtistData,
    ArtistInfo,
    MonthlyListenersData,
    SocialStatsData,
    SpotifyData,
    LabelsData,
    ManagementData
)
from .providers.viberate import ViberateProvider
from .providers.spotify import SpotifyProvider
from .providers.label_resolver import LabelResolver
from .providers.wikidata import WikidataProvider

logger = logging.getLogger(__name__)


class ArtistEnrichmentService:
    """
    Main service for enriching artist data
    Coordinates all providers - Uses Viberate for social stats
    """
    
    def __init__(
        self,
        config: EnrichmentConfig,
        spotify_client_id: str,
        spotify_client_secret: str,
        cache_client=None
    ):
        self.config = config
        self.cache = cache_client
        
        # Initialize providers
        self.viberate_provider = ViberateProvider(config, cache_client)
        self.spotify_provider = SpotifyProvider(
            config,
            spotify_client_id,
            spotify_client_secret,
            cache_client
        )
        self.label_resolver = LabelResolver(config)
        self.wikidata_provider = WikidataProvider(config, cache_client)
    
    def _extract_spotify_id(self, input_str: str) -> str:
        """Extract Spotify artist ID from URL or ID"""
        # If already an ID
        if re.match(r'^[a-zA-Z0-9]{22}$', input_str):
            return input_str
        
        # Extract from URL
        match = re.search(r'artist/([a-zA-Z0-9]{22})', input_str)
        if match:
            return match.group(1)
        
        raise ValueError(f"Invalid Spotify artist ID or URL: {input_str}")
    
    async def enrich(
        self,
        spotify_artist_input: str,
        force_refresh: bool = False
    ) -> EnrichedArtistData:
        """
        Enrich artist data from all sources
        
        Args:
            spotify_artist_input: Spotify artist ID or URL
            force_refresh: Bypass cache
        
        Returns:
            EnrichedArtistData with all information
        """
        spotify_id = self._extract_spotify_id(spotify_artist_input)
        spotify_url = f"https://open.spotify.com/artist/{spotify_id}"
        
        logger.info(f"Starting enrichment for artist {spotify_id}")
        
        notes = []
        
        # 1. Fetch Spotify basic data (parallel safe)
        spotify_data_dict = await self.spotify_provider.get(spotify_id, force_refresh)
        spotify_data = SpotifyData(**spotify_data_dict) if spotify_data_dict else SpotifyData()
        
        if not spotify_data_dict:
            notes.append("Spotify API unavailable - missing genres/followers/popularity")
        
        artist_name = spotify_data_dict.get("name", "Unknown") if spotify_data_dict else "Unknown"
        
        # 2. Fetch Monthly Listeners + Social Stats from Viberate (web scraping)
        viberate_data = await self.viberate_provider.get(spotify_id, artist_name=artist_name, force_refresh=force_refresh)
        
        if viberate_data and viberate_data.get("monthly_listeners"):
            monthly_listeners = MonthlyListenersData(**viberate_data["monthly_listeners"])
        else:
            monthly_listeners = MonthlyListenersData()
            notes.append("Monthly listeners unavailable from Viberate")
        
        if viberate_data and viberate_data.get("social_stats"):
            social_stats = SocialStatsData(**viberate_data["social_stats"])
        else:
            social_stats = SocialStatsData()
            notes.append("Social stats unavailable from Viberate")
        
        # 3. Resolve Labels from Spotify albums
        spotify_albums = await self.spotify_provider.fetch_albums(spotify_id, limit=self.config.label_most_frequent_count)
        labels_dict = self.label_resolver.resolve(spotify_albums=spotify_albums)
        labels = LabelsData(**labels_dict)
        
        if not labels.principal:
            notes.append("Principal label could not be determined")
        
        # 4. Fetch Management from Wikidata
        management_dict = await self.wikidata_provider.get(spotify_id, force_refresh)
        management = ManagementData(**management_dict) if management_dict else ManagementData()
        
        if management.value == "unknown" or not management.value:
            notes.append("Management information not available in Wikidata")
        
        # Assemble final result
        result = EnrichedArtistData(
            artist=ArtistInfo(
                id=spotify_id,
                name=artist_name,
                spotify_id=spotify_id,
                spotify_url=spotify_url
            ),
            monthly_listeners=monthly_listeners,
            social_stats=social_stats,
            spotify=spotify_data,
            labels=labels,
            management=management,
            notes=notes
        )
        
        logger.info(f"Enrichment completed for {spotify_id}: {len(notes)} notes")
        return result
    
    async def enrich_batch(
        self,
        spotify_artist_ids: List[str],
        force_refresh: bool = False
    ) -> List[EnrichedArtistData]:
        """
        Enrich multiple artists in batch
        Uses Viberate web scraping for social stats
        """
        logger.info(f"Starting batch enrichment for {len(spotify_artist_ids)} artists")
        
        # Extract IDs
        artist_ids = [self._extract_spotify_id(aid) for aid in spotify_artist_ids]
        
        # Fetch other data individually (sequential for web scraping rate limits)
        results = []
        for artist_id in artist_ids:
            try:
                # Use main enrich method for each artist
                result = await self.enrich(artist_id, force_refresh)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch enrichment failed for {artist_id}: {e}")
                # Create empty result
                results.append(EnrichedArtistData(
                    artist=ArtistInfo(
                        id=artist_id,
                        name="Unknown",
                        spotify_id=artist_id,
                        spotify_url=f"https://open.spotify.com/artist/{artist_id}"
                    ),
                    monthly_listeners=MonthlyListenersData(),
                    social_stats=SocialStatsData(),
                    spotify=SpotifyData(),
                    labels=LabelsData(),
                    management=ManagementData(),
                    notes=[f"Enrichment failed: {str(e)}"]
                ))
        
        return results
    
    async def close(self):
        """Close all providers"""
        await self.viberate_provider.close()
    
    def get_metrics(self):
        """Get metrics from all providers"""
        return {
            "viberate": self.viberate_provider.get_metrics(),
            "spotify": self.spotify_provider.get_metrics(),
            "wikidata": self.wikidata_provider.get_metrics()
        }
