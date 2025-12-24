"""
Base provider class for data enrichment
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, threshold: int = 5, timeout: int = 60):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "open":
                if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                    self.state = "half_open"
                    logger.info(f"Circuit breaker half-open for {func.__name__}")
                else:
                    raise Exception(f"Circuit breaker open for {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                if self.state == "half_open":
                    self.state = "closed"
                    self.failures = 0
                    logger.info(f"Circuit breaker closed for {func.__name__}")
                return result
            except Exception as e:
                self.failures += 1
                self.last_failure_time = datetime.now()
                
                if self.failures >= self.threshold:
                    self.state = "open"
                    logger.error(f"Circuit breaker opened for {func.__name__}")
                
                raise e
        
        return wrapper


class BaseProvider(ABC):
    """Base class for all enrichment providers"""
    
    def __init__(self, config, cache_client=None):
        self.config = config
        self.cache = cache_client
        self.circuit_breaker = CircuitBreaker(
            threshold=config.circuit_breaker_threshold,
            timeout=config.circuit_breaker_timeout
        )
        self.metrics = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_latency": 0.0
        }
    
    @abstractmethod
    async def fetch(self, artist_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch data from provider"""
        pass
    
    async def get(self, artist_id: str, force_refresh: bool = False, **kwargs) -> Optional[Dict[str, Any]]:
        """Get data with caching and error handling"""
        cache_key = self._cache_key(artist_id)
        
        # Check cache
        if not force_refresh and self.cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                self.metrics["cache_hits"] += 1
                logger.debug(f"{self.__class__.__name__}: Cache hit for {artist_id}")
                return cached
            self.metrics["cache_misses"] += 1
        
        # Fetch with retry
        self.metrics["requests"] += 1
        start_time = datetime.now()
        
        try:
            data = await self._fetch_with_retry(artist_id, **kwargs)
            
            latency = (datetime.now() - start_time).total_seconds()
            self.metrics["total_latency"] += latency
            self.metrics["successes"] += 1
            
            # Cache result
            if data and self.cache:
                await self._set_in_cache(cache_key, data)
            
            logger.info(f"{self.__class__.__name__}: Success for {artist_id} ({latency:.2f}s)")
            return data
            
        except Exception as e:
            self.metrics["failures"] += 1
            logger.error(f"{self.__class__.__name__}: Error for {artist_id}: {e}")
            return None
    
    async def _fetch_with_retry(self, artist_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch with exponential backoff retry"""
        for attempt in range(self.config.max_retries):
            try:
                return await self.circuit_breaker.call(self.fetch)(artist_id, **kwargs)
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    raise
                
                wait_time = self.config.retry_backoff_factor ** attempt
                logger.warning(
                    f"{self.__class__.__name__}: Retry {attempt + 1}/{self.config.max_retries} "
                    f"for {artist_id} after {wait_time}s"
                )
                await asyncio.sleep(wait_time)
    
    def _cache_key(self, artist_id: str) -> str:
        """Generate cache key"""
        return f"{self.__class__.__name__}:{artist_id}"
    
    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get from cache"""
        if not self.cache:
            return None
        # Implement with Redis/similar
        return None
    
    async def _set_in_cache(self, key: str, value: Dict[str, Any]):
        """Set in cache"""
        if not self.cache:
            return
        # Implement with Redis/similar
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get provider metrics"""
        total = self.metrics["requests"]
        return {
            "provider": self.__class__.__name__,
            "requests": total,
            "success_rate": self.metrics["successes"] / total if total > 0 else 0,
            "failure_rate": self.metrics["failures"] / total if total > 0 else 0,
            "cache_hit_rate": self.metrics["cache_hits"] / total if total > 0 else 0,
            "avg_latency": self.metrics["total_latency"] / total if total > 0 else 0,
            "circuit_breaker_state": self.circuit_breaker.state
        }
