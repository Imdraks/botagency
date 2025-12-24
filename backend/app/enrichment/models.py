"""
Data models for artist enrichment
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Evidence trail for data provenance"""
    release_id: Optional[str] = None
    release_name: Optional[str] = None
    release_date: Optional[str] = None
    label: Optional[str] = None


class WikidataEvidence(BaseModel):
    """Wikidata specific evidence"""
    wikidata_entity: Optional[str] = None
    match_property: str = "P1902"  # Spotify artist ID
    management_property: str = "P1037"  # director/manager


class MonthlyListenersData(BaseModel):
    """Monthly listeners information"""
    value: Optional[int] = None
    provider: str = "viberate:scraping"
    retrieved_at: Optional[datetime] = None
    confidence: float = 0.0
    evidence: List[str] = Field(default_factory=list)


class SocialStatsData(BaseModel):
    """Social media followers information from Viberate"""
    spotify_followers: Optional[int] = None
    youtube_subscribers: Optional[int] = None
    instagram_followers: Optional[int] = None
    tiktok_followers: Optional[int] = None
    provider: str = "viberate:scraping"
    retrieved_at: Optional[datetime] = None
    profile_url: Optional[str] = None


class SpotifyData(BaseModel):
    """Spotify API data"""
    genres: List[str] = Field(default_factory=list)
    followers_total: Optional[int] = None
    popularity: Optional[int] = None


class LabelsData(BaseModel):
    """Label information"""
    principal: Optional[str] = None
    method: str = "latest_release"  # or "most_frequent"
    retrieved_at: Optional[datetime] = None
    evidence: List[Evidence] = Field(default_factory=list)


class ManagementData(BaseModel):
    """Management information"""
    value: Optional[str] = None
    provider: str = "wikidata"
    retrieved_at: Optional[datetime] = None
    confidence: float = 0.0
    evidence: Optional[WikidataEvidence] = None


class ArtistInfo(BaseModel):
    """Basic artist info"""
    id: str
    name: str
    spotify_id: str
    spotify_url: str


class EnrichedArtistData(BaseModel):
    """Complete enriched artist data"""
    artist: ArtistInfo
    monthly_listeners: MonthlyListenersData
    social_stats: SocialStatsData = Field(default_factory=SocialStatsData)
    spotify: SpotifyData
    labels: LabelsData
    management: ManagementData
    notes: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class EnrichmentRequest(BaseModel):
    """Request for enriching artist data"""
    spotify_artist_id: Optional[str] = None
    spotify_url: Optional[str] = None
    force_refresh: bool = False


class BatchEnrichmentRequest(BaseModel):
    """Batch enrichment request"""
    artist_ids: List[str]
    force_refresh: bool = False


class EnrichmentStatus(BaseModel):
    """Status of enrichment operation"""
    artist_id: str
    status: str  # pending, processing, completed, failed
    progress: float = 0.0
    error: Optional[str] = None
    result: Optional[EnrichedArtistData] = None
