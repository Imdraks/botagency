"""
Label Resolution Logic
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import Counter

from ..models import Evidence

logger = logging.getLogger(__name__)


class LabelResolver:
    """
    Resolves principal label from Spotify albums
    Two methods: latest_release, most_frequent
    """
    
    def __init__(self, config):
        self.config = config
    
    def resolve(
        self,
        spotify_albums: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Resolve principal label from Spotify albums
        """
        
        # Resolve from Spotify albums
        if spotify_albums:
            return self._resolve_from_spotify(spotify_albums)
        
        return {
            "principal": None,
            "method": self.config.label_resolution_method,
            "retrieved_at": datetime.now(),
            "evidence": []
        }
    
    def _resolve_from_spotify(self, albums: List[Dict]) -> Dict[str, Any]:
        """Resolve from Spotify album data"""
        labeled_albums = []
        
        for album in albums:
            label = album.get("label")
            if not label:
                continue
            
            labeled_albums.append({
                "release_id": album.get("id", ""),
                "release_name": album.get("name", ""),
                "release_date": album.get("release_date", ""),
                "label": label
            })
        
        if not labeled_albums:
            return {
                "principal": None,
                "method": self.config.label_resolution_method,
                "retrieved_at": datetime.now(),
                "evidence": []
            }
        
        # Deduplicate
        unique_albums = self._deduplicate_releases(labeled_albums)
        
        # Sort by date
        sorted_albums = sorted(
            unique_albums,
            key=lambda x: x["release_date"],
            reverse=True
        )
        
        # Apply method
        if self.config.label_resolution_method == "latest_release":
            principal = sorted_albums[0]["label"]
        else:  # most_frequent
            labels = [a["label"] for a in sorted_albums[:self.config.label_most_frequent_count]]
            principal = Counter(labels).most_common(1)[0][0] if labels else None
        
        return {
            "principal": principal,
            "method": self.config.label_resolution_method,
            "retrieved_at": datetime.now(),
            "evidence": [Evidence(**a) for a in sorted_albums[:10]]
        }
    
    def _deduplicate_releases(self, releases: List[Dict]) -> List[Dict]:
        """
        Remove duplicates (deluxe, reissues, multi-markets)
        Strategy: unique by (name, release_date), keep first
        """
        seen = set()
        unique = []
        
        for release in releases:
            # Normalize name (remove "- Deluxe", etc.)
            name = release["release_name"].lower()
            for suffix in [" - deluxe", " - remastered", " - edition", "(deluxe)", "(remastered)"]:
                name = name.replace(suffix, "")
            
            key = (name.strip(), release["release_date"])
            
            if key not in seen:
                seen.add(key)
                unique.append(release)
        
        return unique
