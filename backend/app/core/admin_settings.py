"""
Admin Settings - Dynamic settings that can be changed at runtime
Stored in Redis for persistence across restarts
"""
from typing import Any, Dict, Optional
from app.core.cache import redis_client
import json

ADMIN_SETTINGS_KEY = "admin:settings"

# Default values
DEFAULT_SETTINGS = {
    "send_invitation_emails": True,
}


def get_admin_settings() -> Dict[str, Any]:
    """Get all admin settings"""
    try:
        data = redis_client.get(ADMIN_SETTINGS_KEY)
        if data:
            return {**DEFAULT_SETTINGS, **json.loads(data)}
    except Exception:
        pass
    return DEFAULT_SETTINGS.copy()


def get_admin_setting(key: str, default: Any = None) -> Any:
    """Get a single admin setting"""
    settings = get_admin_settings()
    return settings.get(key, default)


def set_admin_setting(key: str, value: Any) -> Dict[str, Any]:
    """Set a single admin setting"""
    settings = get_admin_settings()
    settings[key] = value
    try:
        redis_client.set(ADMIN_SETTINGS_KEY, json.dumps(settings))
    except Exception:
        pass
    return settings


def set_admin_settings(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update multiple admin settings at once"""
    settings = get_admin_settings()
    settings.update(updates)
    try:
        redis_client.set(ADMIN_SETTINGS_KEY, json.dumps(settings))
    except Exception:
        pass
    return settings
