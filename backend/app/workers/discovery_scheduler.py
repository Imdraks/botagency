"""
Discovery V3 - Scheduled Tasks
Periodic job to generate DiscoveryCandidate feed from computed metrics.
Also generates recommendations based on artist_analyses searches.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from celery import shared_task
from celery.schedules import crontab
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models.discovery import (
    DiscoveryArtist,
    DiscoveryComputedMetrics,
    DiscoveryCandidate,
)
from app.db.models.workspace import Workspace
from app.db.models.artist_analysis import ArtistAnalysis

logger = logging.getLogger(__name__)

# Feed configuration
CANDIDATE_TTL_MINUTES = 1440  # 24 hours
MAX_CANDIDATES_PER_TYPE = 100  # Max candidates per workspace per type


def get_db() -> Session:
    """Get database session."""
    return SessionLocal()


# ============================================================================
# CELERY BEAT SCHEDULE
# ============================================================================

# Add to celery beat schedule (in celery_app.py or here)
DISCOVERY_BEAT_SCHEDULE = {
    'generate-discovery-candidates': {
        'task': 'discovery.generate_candidates',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'cleanup-expired-candidates': {
        'task': 'discovery.cleanup_expired',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
}


# ============================================================================
# MAIN GENERATOR TASK
# ============================================================================

@celery_app.task(name="discovery.generate_candidates")
def generate_discovery_candidates() -> Dict[str, Any]:
    """
    Generate DiscoveryCandidate feed for all active workspaces.
    Runs periodically to keep the feed fresh.
    """
    db = get_db()
    try:
        logger.info("Starting Discovery Candidate generation...")
        
        # Get all workspaces
        workspaces = db.query(Workspace).all()
        
        total_generated = 0
        workspace_stats = {}
        
        for workspace in workspaces:
            try:
                recommended, trending = generate_workspace_candidates(db, workspace.id)
                workspace_stats[workspace.id] = {
                    "recommended": recommended,
                    "trending": trending,
                }
                total_generated += recommended + trending
            except Exception as e:
                logger.error(f"Error generating candidates for workspace {workspace.id}: {e}")
                workspace_stats[workspace.id] = {"error": str(e)}
        
        logger.info(f"Discovery Candidate generation complete. Total: {total_generated}")
        
        return {
            "status": "OK",
            "total_generated": total_generated,
            "workspaces": workspace_stats,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Fatal error in candidate generation: {e}")
        return {"status": "ERROR", "message": str(e)}
    finally:
        db.close()


def generate_workspace_candidates(db: Session, workspace_id: int) -> tuple[int, int]:
    """
    Generate candidates for a single workspace.
    
    Returns: (recommended_count, trending_count)
    """
    logger.info(f"Generating candidates for workspace {workspace_id}")
    
    # TTL for new candidates
    ttl_expires = datetime.utcnow() + timedelta(minutes=CANDIDATE_TTL_MINUTES)
    
    # Get artists with recent computed metrics (last 48h)
    min_computed_date = datetime.utcnow() - timedelta(hours=48)
    
    # Subquery for latest computed metrics per artist
    latest_metrics = db.query(
        DiscoveryComputedMetrics.artist_id,
        DiscoveryComputedMetrics.id.label("metrics_id"),
        DiscoveryComputedMetrics.score,
        DiscoveryComputedMetrics.timing_bucket,
        DiscoveryComputedMetrics.recommendation,
        DiscoveryComputedMetrics.velocity,
        DiscoveryComputedMetrics.acceleration,
        DiscoveryComputedMetrics.data_quality,
        DiscoveryComputedMetrics.drivers,
        DiscoveryComputedMetrics.monthly_listeners,
    ).join(
        DiscoveryArtist,
        DiscoveryComputedMetrics.artist_id == DiscoveryArtist.id
    ).filter(
        DiscoveryArtist.workspace_id == workspace_id,
        DiscoveryArtist.is_deleted == False,
        DiscoveryComputedMetrics.computed_at >= min_computed_date,
    ).distinct(
        DiscoveryComputedMetrics.artist_id
    ).order_by(
        DiscoveryComputedMetrics.artist_id,
        DiscoveryComputedMetrics.computed_at.desc()
    ).all()
    
    if not latest_metrics:
        logger.info(f"No artists with recent metrics for workspace {workspace_id}")
        return 0, 0
    
    # Calculate RECOMMENDED candidates
    recommended_list = []
    for m in latest_metrics:
        rank = calculate_recommended_rank(
            score=m.score,
            timing=m.timing_bucket,
            monthly_listeners=m.monthly_listeners or 0,
            data_quality=m.data_quality,
        )
        reasons = (m.drivers or [])[:2]
        recommended_list.append({
            "artist_id": m.artist_id,
            "rank_score": rank,
            "reasons": reasons,
        })
    
    # Sort and limit
    recommended_list.sort(key=lambda x: x["rank_score"], reverse=True)
    recommended_list = recommended_list[:MAX_CANDIDATES_PER_TYPE]
    
    # Calculate TRENDING candidates
    trending_list = []
    for m in latest_metrics:
        rank = calculate_trending_rank(
            velocity=m.velocity or 0,
            acceleration=m.acceleration or 0,
            score=m.score,
        )
        reasons = []
        if m.velocity and m.velocity > 0.2:
            reasons.append({"label": "Croissance rapide", "value": f"+{int(m.velocity*100)}%/mois", "impact": 15})
        if m.acceleration and m.acceleration > 0.1:
            reasons.append({"label": "Accélération", "value": f"+{int(m.acceleration*100)}%", "impact": 10})
        
        trending_list.append({
            "artist_id": m.artist_id,
            "rank_score": rank,
            "reasons": reasons[:2],
        })
    
    # Sort and limit
    trending_list.sort(key=lambda x: x["rank_score"], reverse=True)
    trending_list = trending_list[:MAX_CANDIDATES_PER_TYPE]
    
    # Delete old candidates for this workspace
    db.query(DiscoveryCandidate).filter(
        DiscoveryCandidate.workspace_id == workspace_id
    ).delete()
    
    # Insert new candidates
    now = datetime.utcnow()
    
    for item in recommended_list:
        candidate = DiscoveryCandidate(
            workspace_id=workspace_id,
            artist_id=item["artist_id"],
            candidate_type="RECOMMENDED",
            rank_score=item["rank_score"],
            reasons=item["reasons"],
            computed_at=now,
            ttl_expires_at=ttl_expires,
        )
        db.add(candidate)
    
    for item in trending_list:
        candidate = DiscoveryCandidate(
            workspace_id=workspace_id,
            artist_id=item["artist_id"],
            candidate_type="TRENDING",
            rank_score=item["rank_score"],
            reasons=item["reasons"],
            computed_at=now,
            ttl_expires_at=ttl_expires,
        )
        db.add(candidate)
    
    db.commit()
    
    logger.info(f"Generated {len(recommended_list)} recommended, {len(trending_list)} trending for workspace {workspace_id}")
    
    return len(recommended_list), len(trending_list)


def calculate_recommended_rank(
    score: int,
    timing: str,
    monthly_listeners: int,
    data_quality: str,
) -> float:
    """
    Calculate rank score for RECOMMENDED feed.
    Higher = better candidate.
    """
    rank = float(score)  # Base: 0-100
    
    # Timing bonus
    timing_bonus = {
        "IMMINENT": 20,
        "1_3M": 15,
        "3_6M": 10,
        "6_12M": 5,
        "LONG": 0,
    }
    rank += timing_bonus.get(timing, 0)
    
    # Sweet spot bonus (10K-100K listeners)
    if 10000 <= monthly_listeners <= 100000:
        rank += 10
    elif monthly_listeners < 10000:
        rank += 5  # Early stage bonus
    elif monthly_listeners > 500000:
        rank -= 15  # Already established
    
    # Data quality bonus
    quality_bonus = {
        "HIGH": 10,
        "MEDIUM": 5,
        "LOW": 0,
    }
    rank += quality_bonus.get(data_quality, 0)
    
    return rank


def calculate_trending_rank(
    velocity: float,
    acceleration: float,
    score: int,
) -> float:
    """
    Calculate rank score for TRENDING feed.
    Based on growth velocity and acceleration.
    """
    rank = 0.0
    
    # Velocity contribution (main factor)
    rank += velocity * 100  # 50% velocity = 50 points
    
    # Acceleration bonus
    if acceleration > 0:
        rank += acceleration * 50  # 20% acceleration = 10 points
    
    # Base score contribution (secondary)
    rank += score * 0.3  # 100 score = 30 points
    
    return rank


# ============================================================================
# CLEANUP TASK
# ============================================================================

@celery_app.task(name="discovery.cleanup_expired")
def cleanup_expired_candidates() -> Dict[str, Any]:
    """
    Clean up expired candidates and old snapshots.
    """
    db = get_db()
    try:
        now = datetime.utcnow()
        
        # Delete expired candidates
        expired_candidates = db.query(DiscoveryCandidate).filter(
            DiscoveryCandidate.ttl_expires_at < now
        ).delete()
        
        # Delete old snapshots (keep last 7 days)
        old_cutoff = now - timedelta(days=7)
        old_snapshots = 0  # We keep snapshots for audit, just log count
        
        db.commit()
        
        logger.info(f"Cleanup: deleted {expired_candidates} expired candidates")
        
        return {
            "status": "OK",
            "expired_candidates_deleted": expired_candidates,
            "cleaned_at": now.isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        db.rollback()
        return {"status": "ERROR", "message": str(e)}
    finally:
        db.close()


# ============================================================================
# MANUAL TRIGGER
# ============================================================================

@celery_app.task(name="discovery.regenerate_workspace")
def regenerate_workspace_candidates(workspace_id: int) -> Dict[str, Any]:
    """
    Manually trigger candidate regeneration for a specific workspace.
    """
    db = get_db()
    try:
        recommended, trending = generate_workspace_candidates(db, workspace_id)
        
        return {
            "status": "OK",
            "workspace_id": workspace_id,
            "recommended": recommended,
            "trending": trending,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error regenerating candidates for workspace {workspace_id}: {e}")
        return {"status": "ERROR", "message": str(e)}
    finally:
        db.close()


# ============================================================================
# RECOMMENDATION ENGINE - Based on artist_analyses searches
# ============================================================================

MAX_RELATED_PER_ARTIST = 10  # Related artists to fetch per seed
MAX_RECOMMENDATIONS = 50  # Max total recommendations per workspace

@celery_app.task(name="discovery.generate_recommendations")
def generate_recommendations() -> Dict[str, Any]:
    """
    Generate artist recommendations based on what users searched in /artist.
    For each workspace:
    1. Look at artist_analyses entries (the user's searches)
    2. Find their Deezer IDs
    3. Fetch related artists from Deezer API
    4. Create DiscoveryArtist + metrics + candidates for suggestions
    """
    db = get_db()
    try:
        logger.info("Starting recommendation generation...")
        
        workspaces = db.query(Workspace).all()
        
        total_generated = 0
        workspace_stats = {}
        
        for workspace in workspaces:
            try:
                count = generate_workspace_recommendations(db, workspace.id)
                workspace_stats[workspace.id] = count
                total_generated += count
            except Exception as e:
                logger.error(f"Recommendation error for workspace {workspace.id}: {e}")
                workspace_stats[workspace.id] = {"error": str(e)}
        
        logger.info(f"Recommendation generation complete. Total: {total_generated}")
        
        return {
            "status": "OK",
            "total_generated": total_generated,
            "workspaces": workspace_stats,
        }
    except Exception as e:
        logger.error(f"Fatal recommendation error: {e}")
        return {"status": "ERROR", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="discovery.generate_recommendations_workspace")
def generate_recommendations_for_workspace(workspace_id: int) -> Dict[str, Any]:
    """Trigger recommendation generation for a single workspace."""
    db = get_db()
    try:
        count = generate_workspace_recommendations(db, workspace_id)
        return {"status": "OK", "workspace_id": workspace_id, "generated": count}
    except Exception as e:
        logger.error(f"Recommendation error for workspace {workspace_id}: {e}")
        return {"status": "ERROR", "message": str(e)}
    finally:
        db.close()


def generate_workspace_recommendations(db: Session, workspace_id: int) -> int:
    """
    Generate recommendations for a workspace based on its artist_analyses.
    Returns count of new candidates created.
    """
    from app.enrichment.providers.deezer import search_deezer_artist, fetch_related_artists
    
    # 1. Get all artist names searched by the user in this workspace
    seed_artists = db.query(ArtistAnalysis).filter(
        ArtistAnalysis.workspace_id == workspace_id,
    ).all()
    
    if not seed_artists:
        logger.info(f"No seed artists for workspace {workspace_id}")
        return 0
    
    logger.info(f"Workspace {workspace_id}: {len(seed_artists)} seed artists")
    
    # 2. Get existing normalized names to avoid duplicates
    existing_discovery = db.query(DiscoveryArtist.normalized_name).filter(
        DiscoveryArtist.workspace_id == workspace_id,
        DiscoveryArtist.is_deleted == False,
    ).all()
    existing_names = {row[0] for row in existing_discovery}
    
    existing_analyses = db.query(ArtistAnalysis.artist_name).filter(
        ArtistAnalysis.workspace_id == workspace_id,
    ).all()
    searched_names = {_normalize(row[0]) for row in existing_analyses}
    
    # Combine: skip artists already known
    skip_names = existing_names | searched_names
    
    # 3. For each seed, find related artists via Deezer
    all_related: Dict[str, Dict[str, Any]] = {}  # normalized_name -> data
    
    for seed in seed_artists:
        try:
            # Find Deezer ID for this artist
            dz_data = search_deezer_artist(seed.artist_name)
            if not dz_data or not dz_data.get("deezer_id"):
                continue
            
            deezer_id = dz_data["deezer_id"]
            
            # Fetch related artists
            related = fetch_related_artists(deezer_id, limit=MAX_RELATED_PER_ARTIST)
            
            for r in related:
                norm = _normalize(r.get("name", ""))
                if not norm or norm in skip_names or norm in all_related:
                    continue
                
                r["seed_artist"] = seed.artist_name
                r["seed_listeners"] = seed.spotify_monthly_listeners or 0
                all_related[norm] = r
                
        except Exception as e:
            logger.warning(f"Failed to get related for '{seed.artist_name}': {e}")
    
    if not all_related:
        logger.info(f"No new related artists found for workspace {workspace_id}")
        return 0
    
    # 4. Limit to top N by fans
    sorted_related = sorted(
        all_related.values(),
        key=lambda x: x.get("deezer_fans", 0),
        reverse=True,
    )[:MAX_RECOMMENDATIONS]
    
    # 5. Create DiscoveryArtist + metrics + candidates
    now = datetime.utcnow()
    ttl_expires = now + timedelta(hours=24)
    created = 0
    
    for r in sorted_related:
        try:
            name = r.get("name", "").strip()
            norm = _normalize(name)
            
            # Create DiscoveryArtist
            artist = DiscoveryArtist(
                workspace_id=workspace_id,
                canonical_name=name,
                normalized_name=norm,
                image_url=r.get("image_url"),
                data_quality="LOW",
            )
            db.add(artist)
            db.flush()
            
            # Create lightweight metrics from Deezer data
            fans = r.get("deezer_fans", 0)
            score = _estimate_score_from_fans(fans)
            timing = _estimate_timing(fans)
            
            metrics = DiscoveryComputedMetrics(
                artist_id=artist.id,
                score=score,
                timing_bucket=timing,
                recommendation="WATCH" if score >= 40 else "IGNORE",
                drivers=[
                    {"label": "Artiste similaire", "value": f"Basé sur {r['seed_artist']}", "impact": 15},
                    {"label": "Fans Deezer", "value": f"{fans:,}", "impact": 10},
                ],
                penalties=[],
                monthly_listeners=0,  # Not yet scraped
                spotify_followers=0,
                total_social_followers=fans,
                data_quality="LOW",
                algo_version="v3.0-reco",
                computed_at=now,
            )
            db.add(metrics)
            db.flush()
            
            # Create RECOMMENDED candidate
            rec_rank = calculate_recommended_rank(
                score=score,
                timing=timing,
                monthly_listeners=0,
                data_quality="LOW",
            )
            db.add(DiscoveryCandidate(
                workspace_id=workspace_id,
                artist_id=artist.id,
                candidate_type="RECOMMENDED",
                rank_score=rec_rank,
                reasons=[
                    {"label": "Artiste similaire", "value": f"Basé sur {r['seed_artist']}", "impact": 15},
                ],
                computed_at=now,
                ttl_expires_at=ttl_expires,
            ))
            
            created += 1
            
        except Exception as e:
            logger.warning(f"Failed to create recommendation for '{r.get('name')}': {e}")
            db.rollback()
            continue
    
    db.commit()
    logger.info(f"Created {created} recommendations for workspace {workspace_id}")
    return created


def _normalize(name: str) -> str:
    """Normalize artist name for dedup."""
    import unicodedata
    import re
    name = name.lower().strip()
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def _estimate_score_from_fans(deezer_fans: int) -> int:
    """Estimate a discovery score from Deezer fan count."""
    if deezer_fans >= 5_000_000:
        return 25  # Too big, low discovery value
    elif deezer_fans >= 1_000_000:
        return 40
    elif deezer_fans >= 200_000:
        return 55
    elif deezer_fans >= 50_000:
        return 65
    elif deezer_fans >= 10_000:
        return 75  # Sweet spot: enough traction + growth potential
    elif deezer_fans >= 1_000:
        return 60
    else:
        return 35  # Too small


def _estimate_timing(deezer_fans: int) -> str:
    """Estimate timing bucket from fan count."""
    if deezer_fans >= 200_000:
        return "IMMINENT"
    elif deezer_fans >= 50_000:
        return "1_3M"
    elif deezer_fans >= 10_000:
        return "3_6M"
    else:
        return "LONG"
