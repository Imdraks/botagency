"""
Middleware de Rate Limiting
Protection contre les abus d'API avec quotas par utilisateur
"""
import logging
import time
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import asyncio

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration du rate limiting"""
    # Limites par défaut (requêtes par fenêtre)
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    
    # Limites pour endpoints spécifiques
    heavy_endpoints_per_minute: int = 10  # Export, scoring batch, etc.
    auth_endpoints_per_minute: int = 10   # Login, register
    
    # Limites par rôle
    admin_multiplier: float = 2.0
    
    # Whitelist d'IPs (pas de limite)
    ip_whitelist: list = None
    
    # Endpoints lourds
    heavy_endpoints: list = None
    
    # Endpoints d'auth
    auth_endpoints: list = None
    
    def __post_init__(self):
        if self.ip_whitelist is None:
            self.ip_whitelist = ["127.0.0.1", "::1"]
        
        if self.heavy_endpoints is None:
            self.heavy_endpoints = [
                "/api/export",
                "/api/scoring/opportunities/rescore",
                "/api/collection",
                "/api/enrichment/batch",
            ]
        
        if self.auth_endpoints is None:
            self.auth_endpoints = [
                "/api/auth/login",
                "/api/auth/register",
                "/api/auth/reset-password",
            ]


class RateLimiter:
    """
    Rate limiter en mémoire avec fenêtres glissantes.
    Pour production, utiliser Redis pour le stockage distribué.
    """
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        
        # Stockage: {key: [(timestamp, count), ...]}
        self._minute_windows: Dict[str, list] = defaultdict(list)
        self._hour_windows: Dict[str, list] = defaultdict(list)
        self._day_windows: Dict[str, list] = defaultdict(list)
        
        # Lock pour thread-safety
        self._lock = asyncio.Lock()
        
        # Cleanup task
        self._cleanup_interval = 60  # seconds
        self._last_cleanup = time.time()
    
    def _get_key(self, request: Request) -> str:
        """Génère une clé unique pour le client"""
        # Priorité: user_id > IP
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fallback sur IP
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Récupère l'IP du client (avec support proxy)"""
        # Headers de proxy courants
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_whitelisted(self, request: Request) -> bool:
        """Vérifie si l'IP est whitelistée"""
        client_ip = self._get_client_ip(request)
        return client_ip in self.config.ip_whitelist
    
    def _get_endpoint_type(self, path: str) -> str:
        """Détermine le type d'endpoint"""
        for heavy in self.config.heavy_endpoints:
            if path.startswith(heavy):
                return "heavy"
        
        for auth in self.config.auth_endpoints:
            if path.startswith(auth):
                return "auth"
        
        return "normal"
    
    def _cleanup_old_entries(self):
        """Nettoie les anciennes entrées"""
        now = time.time()
        
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        
        # Nettoyer les fenêtres de minute (> 1 min)
        minute_cutoff = now - 60
        for key in list(self._minute_windows.keys()):
            self._minute_windows[key] = [
                (ts, c) for ts, c in self._minute_windows[key] 
                if ts > minute_cutoff
            ]
            if not self._minute_windows[key]:
                del self._minute_windows[key]
        
        # Nettoyer les fenêtres d'heure (> 1h)
        hour_cutoff = now - 3600
        for key in list(self._hour_windows.keys()):
            self._hour_windows[key] = [
                (ts, c) for ts, c in self._hour_windows[key] 
                if ts > hour_cutoff
            ]
            if not self._hour_windows[key]:
                del self._hour_windows[key]
        
        # Nettoyer les fenêtres de jour (> 24h)
        day_cutoff = now - 86400
        for key in list(self._day_windows.keys()):
            self._day_windows[key] = [
                (ts, c) for ts, c in self._day_windows[key] 
                if ts > day_cutoff
            ]
            if not self._day_windows[key]:
                del self._day_windows[key]
    
    def _count_in_window(self, entries: list, window_seconds: int) -> int:
        """Compte les requêtes dans une fenêtre"""
        cutoff = time.time() - window_seconds
        return sum(count for ts, count in entries if ts > cutoff)
    
    async def check_rate_limit(
        self, 
        request: Request,
        is_admin: bool = False
    ) -> Optional[Dict]:
        """
        Vérifie si la requête est autorisée.
        
        Returns:
            None si autorisé, sinon dict avec infos d'erreur
        """
        # Whitelist check
        if self._is_whitelisted(request):
            return None
        
        async with self._lock:
            self._cleanup_old_entries()
            
            key = self._get_key(request)
            now = time.time()
            endpoint_type = self._get_endpoint_type(request.url.path)
            
            # Multiplicateur admin
            multiplier = self.config.admin_multiplier if is_admin else 1.0
            
            # Limites selon le type d'endpoint
            if endpoint_type == "heavy":
                minute_limit = int(self.config.heavy_endpoints_per_minute * multiplier)
            elif endpoint_type == "auth":
                minute_limit = self.config.auth_endpoints_per_minute
            else:
                minute_limit = int(self.config.requests_per_minute * multiplier)
            
            hour_limit = int(self.config.requests_per_hour * multiplier)
            day_limit = int(self.config.requests_per_day * multiplier)
            
            # Vérifier les limites
            minute_count = self._count_in_window(self._minute_windows[key], 60)
            if minute_count >= minute_limit:
                retry_after = 60 - (now - self._minute_windows[key][0][0]) if self._minute_windows[key] else 60
                return {
                    "error": "Rate limit exceeded",
                    "limit": minute_limit,
                    "window": "minute",
                    "retry_after": int(retry_after),
                    "current": minute_count
                }
            
            hour_count = self._count_in_window(self._hour_windows[key], 3600)
            if hour_count >= hour_limit:
                return {
                    "error": "Rate limit exceeded",
                    "limit": hour_limit,
                    "window": "hour",
                    "retry_after": 3600,
                    "current": hour_count
                }
            
            day_count = self._count_in_window(self._day_windows[key], 86400)
            if day_count >= day_limit:
                return {
                    "error": "Rate limit exceeded",
                    "limit": day_limit,
                    "window": "day",
                    "retry_after": 86400,
                    "current": day_count
                }
            
            # Enregistrer la requête
            self._minute_windows[key].append((now, 1))
            self._hour_windows[key].append((now, 1))
            self._day_windows[key].append((now, 1))
            
            return None
    
    def get_usage_stats(self, key: str) -> Dict:
        """Retourne les stats d'utilisation pour une clé"""
        return {
            "minute": self._count_in_window(self._minute_windows.get(key, []), 60),
            "hour": self._count_in_window(self._hour_windows.get(key, []), 3600),
            "day": self._count_in_window(self._day_windows.get(key, []), 86400),
            "limits": {
                "minute": self.config.requests_per_minute,
                "hour": self.config.requests_per_hour,
                "day": self.config.requests_per_day
            }
        }


# Instance globale
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware FastAPI pour le rate limiting"""
    
    def __init__(self, app, limiter: RateLimiter = None, enabled: bool = True):
        super().__init__(app)
        self.limiter = limiter or rate_limiter
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip si désactivé
        if not self.enabled:
            return await call_next(request)
        
        # Skip pour les health checks
        if request.url.path in ["/health", "/api/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Vérifier si l'utilisateur est admin (si authentifié)
        is_admin = getattr(request.state, 'is_admin', False)
        
        # Vérifier le rate limit
        result = await self.limiter.check_rate_limit(request, is_admin=is_admin)
        
        if result:
            logger.warning(
                f"Rate limit exceeded: {self.limiter._get_key(request)} "
                f"- {result['window']}: {result['current']}/{result['limit']}"
            )
            
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "error": result["error"],
                    "limit": result["limit"],
                    "window": result["window"],
                    "retry_after": result["retry_after"]
                }
            )
            response.headers["Retry-After"] = str(result["retry_after"])
            response.headers["X-RateLimit-Limit"] = str(result["limit"])
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + result["retry_after"])
            
            return response
        
        # Ajouter les headers de rate limit à la réponse
        response = await call_next(request)
        
        # Ajouter les headers informatifs
        key = self.limiter._get_key(request)
        stats = self.limiter.get_usage_stats(key)
        
        response.headers["X-RateLimit-Limit"] = str(stats["limits"]["minute"])
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, stats["limits"]["minute"] - stats["minute"])
        )
        
        return response


def get_rate_limiter() -> RateLimiter:
    """Dependency pour obtenir le rate limiter"""
    return rate_limiter
