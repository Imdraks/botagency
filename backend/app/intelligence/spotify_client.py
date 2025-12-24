"""
Spotify API Client pour récupérer les données d'artistes
Intègre le scraping Viberate pour monthly listeners et social stats réels
"""
import logging
from typing import Optional, Dict, Any
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from app.core.config import settings

logger = logging.getLogger(__name__)


class SpotifyClient:
    """Client pour interagir avec l'API Spotify"""
    
    def __init__(self):
        self.client = None
        self._initialized = False
        self._enrichment_service = None
        self._init_client()
        self._init_enrichment()
    
    def _init_client(self):
        """Initialise le client Spotify si les credentials sont disponibles"""
        if not settings.spotify_client_id or not settings.spotify_client_secret:
            logger.warning("Spotify credentials not configured. Spotify API will not be available.")
            return
        
        try:
            auth_manager = SpotifyClientCredentials(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret
            )
            self.client = spotipy.Spotify(auth_manager=auth_manager)
            self._initialized = True
            logger.info("✅ Spotify API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
    
    def _init_enrichment(self):
        """Initialise le service d'enrichissement Viberate si disponible"""
        try:
            from app.enrichment.config import EnrichmentConfig
            from app.enrichment.service import ArtistEnrichmentService
            
            if not settings.viberate_enabled:
                logger.info("Viberate scraping disabled. Using estimated monthly listeners.")
                return
            
            enrichment_config = EnrichmentConfig(
                viberate_enabled=settings.viberate_enabled,
                viberate_request_delay=settings.viberate_request_delay
            )
            
            self._enrichment_service = ArtistEnrichmentService(
                config=enrichment_config,
                spotify_client_id=settings.spotify_client_id,
                spotify_client_secret=settings.spotify_client_secret
            )
            logger.info("✅ Viberate enrichment service initialized successfully")
        except ImportError:
            logger.debug("Enrichment module not available")
        except Exception as e:
            logger.warning(f"Failed to initialize enrichment service: {e}")
    
    def is_available(self) -> bool:
        """Vérifie si le client Spotify est disponible"""
        return self._initialized and self.client is not None
    
    def _normalize_name(self, name: str) -> str:
        """Normalise un nom pour la comparaison"""
        import unicodedata
        # Mettre en minuscule et supprimer les accents
        name = name.lower().strip()
        name = unicodedata.normalize('NFD', name)
        name = ''.join(c for c in name if not unicodedata.combining(c))
        # Supprimer les caractères spéciaux
        name = ''.join(c for c in name if c.isalnum() or c.isspace())
        return name
    
    def _find_best_match(self, search_name: str, artists: list) -> Optional[Dict[str, Any]]:
        """
        Trouve le meilleur match parmi les résultats de recherche.
        Utilise plusieurs critères : correspondance exacte du nom, popularité, followers.
        """
        if not artists:
            return None
        
        search_normalized = self._normalize_name(search_name)
        
        candidates = []
        for artist in artists:
            artist_name = artist['name']
            artist_normalized = self._normalize_name(artist_name)
            
            # Score de correspondance
            score = 0
            
            # Correspondance exacte (priorité maximale)
            if artist_normalized == search_normalized:
                score += 1000
            # Le nom contient la recherche exacte
            elif search_normalized in artist_normalized or artist_normalized in search_normalized:
                score += 500
            # Mots communs
            else:
                search_words = set(search_normalized.split())
                artist_words = set(artist_normalized.split())
                common_words = search_words & artist_words
                if common_words:
                    score += len(common_words) * 100
            
            # Bonus pour popularité et followers (artistes plus connus)
            score += artist['popularity'] * 2  # 0-200 points
            score += min(artist['followers']['total'] / 10000, 100)  # 0-100 points
            
            candidates.append((score, artist))
            logger.debug(f"  Match candidate: {artist_name} (pop:{artist['popularity']}, followers:{artist['followers']['total']:,}, score:{score:.0f})")
        
        # Trier par score décroissant
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        if candidates:
            best = candidates[0][1]
            logger.info(f"🎯 Best match for '{search_name}': {best['name']} (pop:{best['popularity']}, followers:{best['followers']['total']:,})")
            return best
        
        return None
    
    def _estimate_monthly_listeners(self, followers: int, popularity: int) -> int:
        """
        Estime les monthly listeners basé sur followers et popularité
        En général: monthly listeners = followers * multiplicateur
        - Artistes très populaires (pop 80+): 3-4x followers
        - Artistes populaires (pop 60-80): 2-3x followers  
        - Artistes moyens (pop 40-60): 1.5-2x followers
        - Artistes émergents (pop <40): 1-1.5x followers
        """
        if popularity >= 80:
            multiplier = 3.5
        elif popularity >= 70:
            multiplier = 3.0
        elif popularity >= 60:
            multiplier = 2.5
        elif popularity >= 50:
            multiplier = 2.0
        elif popularity >= 40:
            multiplier = 1.5
        else:
            multiplier = 1.2
        
        return int(followers * multiplier)
    
    def search_artist(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un artiste sur Spotify avec enrichissement optionnel
        
        Args:
            artist_name: Nom de l'artiste à rechercher
            
        Returns:
            Dict avec les informations de l'artiste (avec monthly listeners réels si disponible)
        """
        if not self.is_available():
            logger.debug("Spotify API not available")
            return None
        
        try:
            # Recherche de l'artiste
            results = self.client.search(q=f'artist:{artist_name}', type='artist', limit=10)
            
            if not results['artists']['items']:
                logger.debug(f"No Spotify results for: {artist_name}")
                return None
            
            # Trouver le meilleur match (pas juste le premier)
            artist = self._find_best_match(artist_name, results['artists']['items'])
            
            if not artist:
                logger.warning(f"No good match found for: {artist_name}")
                return None
            
            artist_id = artist['id']
            
            # Extraire les données de base
            artist_data = {
                'id': artist_id,
                'name': artist['name'],
                'followers': artist['followers']['total'],
                'popularity': artist['popularity'],  # 0-100
                'genres': artist['genres'],
                'spotify_url': artist['external_urls']['spotify'],
                'image_url': artist['images'][0]['url'] if artist['images'] else None,
            }
            
            # Tenter d'obtenir monthly listeners + social stats via Viberate
            monthly_listeners = None
            social_stats = None
            source = "estimated"
            
            if self._enrichment_service:
                try:
                    import asyncio
                    # Récupérer monthly listeners + social stats réels via Viberate
                    enriched = asyncio.run(self._enrichment_service.enrich(artist_id, force_refresh=False))
                    if enriched.monthly_listeners.value:
                        monthly_listeners = enriched.monthly_listeners.value
                        source = "viberate"
                        logger.info(f"✅ Real monthly listeners from Viberate: {monthly_listeners:,}")
                    
                    # Récupérer les social stats
                    if enriched.social_stats:
                        social_stats = {
                            'spotify_followers': enriched.social_stats.spotify_followers,
                            'youtube_subscribers': enriched.social_stats.youtube_subscribers,
                            'instagram_followers': enriched.social_stats.instagram_followers,
                            'tiktok_followers': enriched.social_stats.tiktok_followers,
                        }
                        logger.info(f"✅ Social stats from Viberate: {social_stats}")
                except Exception as e:
                    logger.debug(f"Could not get data from Viberate: {e}")
            
            # Fallback sur estimation si enrichissement non disponible
            if monthly_listeners is None:
                monthly_listeners = self._estimate_monthly_listeners(
                    artist['followers']['total'], 
                    artist['popularity']
                )
                logger.debug(f"Using estimated monthly listeners: {monthly_listeners:,}")
            
            artist_data['monthly_listeners'] = monthly_listeners
            artist_data['monthly_listeners_source'] = source
            artist_data['estimated_monthly_listeners'] = monthly_listeners  # Pour compatibilité
            
            # Ajouter les social stats si disponibles
            if social_stats:
                artist_data['social_stats'] = social_stats
            
            logger.info(f"✅ Found Spotify artist: {artist_data['name']} - {artist_data['followers']:,} followers, {monthly_listeners:,} monthly listeners ({source})")
            return artist_data
            
        except Exception as e:
            logger.error(f"Error searching Spotify for {artist_name}: {e}")
            return None
    
    async def search_artist_async(self, artist_name: str, use_enrichment: bool = True) -> Optional[Dict[str, Any]]:
        """
        Version async de search_artist avec enrichissement
        
        Args:
            artist_name: Nom de l'artiste
            use_enrichment: Utiliser l'enrichissement pour monthly listeners réels
            
        Returns:
            Dict avec informations enrichies
        """
        if not self.is_available():
            return None
        
        try:
            # Recherche de base
            results = self.client.search(q=f'artist:{artist_name}', type='artist', limit=5)
            if not results['artists']['items']:
                return None
            
            artist = results['artists']['items'][0]
            artist_id = artist['id']
            
            artist_data = {
                'id': artist_id,
                'name': artist['name'],
                'followers': artist['followers']['total'],
                'popularity': artist['popularity'],
                'genres': artist['genres'],
                'spotify_url': artist['external_urls']['spotify'],
                'image_url': artist['images'][0]['url'] if artist['images'] else None,
            }
            
            # Enrichissement async
            if use_enrichment and self._enrichment_service:
                try:
                    enriched = await self._enrichment_service.enrich(artist_id, force_refresh=False)
                    
                    # Monthly listeners réels
                    if enriched.monthly_listeners.value:
                        artist_data['monthly_listeners'] = enriched.monthly_listeners.value
                        artist_data['monthly_listeners_source'] = 'viberate'
                    
                    # Label principal
                    if enriched.labels.principal:
                        artist_data['label'] = enriched.labels.principal
                    
                    # Management
                    if enriched.management.value:
                        artist_data['management'] = enriched.management.value
                    
                    logger.info(f"✅ Enriched data: {artist_data['name']} - {artist_data.get('monthly_listeners', 0):,} listeners")
                except Exception as e:
                    logger.debug(f"Enrichment failed, using estimates: {e}")
            
            # Fallback sur estimation
            if 'monthly_listeners' not in artist_data:
                artist_data['monthly_listeners'] = self._estimate_monthly_listeners(
                    artist['followers']['total'],
                    artist['popularity']
                )
                artist_data['monthly_listeners_source'] = 'estimated'
            
            artist_data['estimated_monthly_listeners'] = artist_data['monthly_listeners']
            
            return artist_data
            
        except Exception as e:
            logger.error(f"Error in async search: {e}")
            return None
    
    def get_artist_top_tracks(self, artist_id: str, country: str = 'FR') -> list:
        """
        Récupère les top tracks d'un artiste
        
        Args:
            artist_id: ID Spotify de l'artiste
            country: Code pays (FR, US, etc.)
            
        Returns:
            Liste des top tracks
        """
        if not self.is_available():
            return []
        
        try:
            results = self.client.artist_top_tracks(artist_id, country=country)
            return results['tracks']
        except Exception as e:
            logger.error(f"Error getting top tracks: {e}")
            return []
    
    def get_artist_albums(self, artist_id: str, limit: int = 10) -> list:
        """
        Récupère les albums d'un artiste
        
        Args:
            artist_id: ID Spotify de l'artiste
            limit: Nombre maximum d'albums à récupérer
            
        Returns:
            Liste des albums
        """
        if not self.is_available():
            return []
        
        try:
            results = self.client.artist_albums(
                artist_id, 
                album_type='album,single',
                limit=limit,
                country='FR'
            )
            return results['items']
        except Exception as e:
            logger.error(f"Error getting albums: {e}")
            return []
    
    def get_monthly_listeners(self, artist_id: str) -> Optional[int]:
        """
        Tente de récupérer le nombre d'auditeurs mensuels
        Note: Cette donnée n'est pas directement disponible dans l'API standard
        On peut l'estimer avec popularité et followers
        
        Args:
            artist_id: ID Spotify de l'artiste
            
        Returns:
            Estimation des auditeurs mensuels ou None
        """
        # L'API Spotify ne fournit pas directement les monthly listeners
        # On peut estimer avec une formule basée sur popularité et followers
        try:
            artist = self.client.artist(artist_id)
            followers = artist['followers']['total']
            popularity = artist['popularity']
            
            # Formule d'estimation (basée sur observations)
            # Plus l'artiste est populaire, plus le ratio listeners/followers est élevé
            if popularity >= 80:
                ratio = 10  # Très populaire
            elif popularity >= 60:
                ratio = 6   # Populaire
            elif popularity >= 40:
                ratio = 3   # Moyenne
            else:
                ratio = 1.5 # Émergent
            
            estimated_listeners = int(followers * ratio)
            logger.debug(f"Estimated monthly listeners: {estimated_listeners:,} (followers={followers:,}, popularity={popularity})")
            return estimated_listeners
            
        except Exception as e:
            logger.error(f"Error estimating monthly listeners: {e}")
            return None


# Instance globale
spotify_client = SpotifyClient()
