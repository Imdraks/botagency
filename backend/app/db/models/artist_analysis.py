"""
Model for storing artist analysis history
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from app.db.base import Base


class ArtistAnalysis(Base):
    """Historique des analyses d'artistes"""
    __tablename__ = "artist_analyses"

    id = Column(Integer, primary_key=True, index=True)
    
    # Artiste info
    artist_name = Column(String(255), nullable=False, index=True)
    real_name = Column(String(255), nullable=True)
    genre = Column(String(100), nullable=True)
    image_url = Column(String(500), nullable=True)  # Photo de l'artiste
    
    # Métriques sociales
    spotify_monthly_listeners = Column(Integer, default=0)
    youtube_subscribers = Column(Integer, default=0)
    instagram_followers = Column(Integer, default=0)
    tiktok_followers = Column(Integer, default=0)
    total_followers = Column(Integer, default=0)
    
    # Estimation financière
    fee_min = Column(Float, default=0)
    fee_max = Column(Float, default=0)
    market_tier = Column(String(50), nullable=True)
    popularity_score = Column(Float, default=0)
    
    # Business
    record_label = Column(String(255), nullable=True)
    management = Column(String(255), nullable=True)
    booking_agency = Column(String(255), nullable=True)
    booking_email = Column(String(255), nullable=True)
    
    # Analyse classique
    market_trend = Column(String(50), default="stable")
    confidence_score = Column(Float, default=0)
    
    # === NEW: AI Intelligence Fields ===
    # Score IA global (0-100)
    ai_score = Column(Float, default=0)
    ai_tier = Column(String(50), nullable=True)  # superstar, major, established, rising, emerging, underground
    
    # Prédictions de croissance
    growth_trend = Column(String(50), nullable=True)  # explosive, rapid, strong, moderate, stable, declining, falling
    predicted_listeners_30d = Column(Integer, nullable=True)
    predicted_listeners_90d = Column(Integer, nullable=True)
    predicted_listeners_180d = Column(Integer, nullable=True)
    growth_rate_monthly = Column(Float, nullable=True)  # % de croissance mensuelle
    
    # Analyse SWOT
    strengths = Column(JSON, nullable=True)  # List[str]
    weaknesses = Column(JSON, nullable=True)  # List[str]
    opportunities = Column(JSON, nullable=True)  # List[str]
    threats = Column(JSON, nullable=True)  # List[str]
    
    # Booking Intelligence
    optimal_fee = Column(Float, nullable=True)
    negotiation_power = Column(String(50), nullable=True)  # low, medium, high
    best_booking_window = Column(String(100), nullable=True)
    event_type_fit = Column(JSON, nullable=True)  # Dict[str, float]
    territory_strength = Column(JSON, nullable=True)  # Dict[str, float]
    seasonal_demand = Column(JSON, nullable=True)  # Dict[str, float]
    
    # Risk & Opportunity
    risk_score = Column(Float, nullable=True)  # 0-1
    risk_factors = Column(JSON, nullable=True)  # List[str]
    opportunity_score = Column(Float, nullable=True)  # 0-1
    key_opportunities = Column(JSON, nullable=True)  # List[str]
    
    # Content Strategy
    best_platforms = Column(JSON, nullable=True)  # List[str]
    engagement_rate = Column(Float, nullable=True)
    viral_potential = Column(Float, nullable=True)
    content_recommendations = Column(JSON, nullable=True)  # List[str]
    
    # AI Summary
    ai_summary = Column(Text, nullable=True)
    ai_recommendations = Column(JSON, nullable=True)  # List[str]
    
    # Données complètes JSON
    full_data = Column(JSON, nullable=True)
    ai_report = Column(JSON, nullable=True)  # Full AI intelligence report
    
    # Métadonnées
    sources_scanned = Column(Text, nullable=True)  # Comma-separated list
    analyzed_by_user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ArtistAnalysis {self.artist_name} - Score:{self.ai_score} - {self.fee_min}-{self.fee_max}€>"
