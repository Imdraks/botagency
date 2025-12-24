"""
Configuration for enrichment providers
"""
from pydantic_settings import BaseSettings


class EnrichmentConfig(BaseSettings):
    """Enrichment service configuration"""
    
    # Viberate Web Scraping
    viberate_enabled: bool = True
    viberate_request_delay: float = 1.5  # seconds between requests (rate limiting)
    timeout_viberate: int = 30  # seconds
    
    # Cache TTLs (seconds)
    cache_ttl_monthly_listeners: int = 3600  # 1 hour - changes frequently
    cache_ttl_social_stats: int = 3600  # 1 hour - social followers
    cache_ttl_labels: int = 86400  # 24 hours - changes rarely
    cache_ttl_management: int = 604800  # 7 days - almost never changes
    cache_ttl_spotify_data: int = 86400  # 24 hours
    
    # Retry & Circuit Breaker
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    circuit_breaker_threshold: int = 5  # failures before opening
    circuit_breaker_timeout: int = 60  # seconds before half-open
    
    # Timeouts
    timeout_spotify: int = 10
    timeout_wikidata: int = 15
    
    # Label Resolution
    label_resolution_method: str = "latest_release"  # or "most_frequent"
    label_most_frequent_count: int = 20  # for most_frequent method
    
    # Batch Processing
    batch_size: int = 50
    batch_concurrency: int = 5
    
    class Config:
        env_prefix = "ENRICHMENT_"
