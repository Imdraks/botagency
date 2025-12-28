"""
Celery tasks for Radar features:
- Daily Shortlist generation
- Cluster rebuild (deduplication)
- Deadline Guard alerts
- Source Health rollup
- Contact Finder (on-demand)
"""
import asyncio
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
import hashlib
import re
from collections import defaultdict

from celery import shared_task
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.workers.task_logger import get_task_logger, Colors
from app.db.session import SessionLocal
from app.db.models.opportunity import Opportunity, OpportunityStatus
from app.db.models.source import SourceConfig
from app.db.models.radar_features import (
    Profile, OpportunityProfileScore, DailyShortlist,
    OpportunityCluster, OpportunityClusterMember,
    DeadlineAlert, AlertType, AlertStatus,
    SourceHealth, ContactFinderResult
)
from app.core.config import settings


def get_db() -> Session:
    """Get database session"""
    return SessionLocal()


# ============================================================================
# DAILY SHORTLIST - Génération quotidienne des meilleures opportunités
# ============================================================================

def compute_fit_score(opportunity: Opportunity, profile: Profile) -> float:
    """
    Calculate fit score for an opportunity based on profile weights.
    Returns score 0-100.
    """
    weights = profile.weights or {}
    score = 0.0
    total_weight = 0.0
    
    # Score based on opportunity's existing score
    if opportunity.score is not None:
        base_score = opportunity.score
    else:
        base_score = 50.0
    
    # Weight factors
    w_score = weights.get('score_weight', 0.3)
    w_budget = weights.get('budget_weight', 0.2)
    w_deadline = weights.get('deadline_weight', 0.2)
    w_category = weights.get('category_weight', 0.15)
    w_source = weights.get('source_weight', 0.15)
    
    # Score contribution
    score += base_score * w_score
    total_weight += w_score
    
    # Budget contribution
    if opportunity.budget_amount and profile.criteria:
        target_min = profile.criteria.get('budget_min', 0)
        target_max = profile.criteria.get('budget_max', float('inf'))
        if target_min <= opportunity.budget_amount <= target_max:
            score += 100 * w_budget
        elif opportunity.budget_amount > 0:
            # Partial score based on proximity
            if opportunity.budget_amount < target_min:
                ratio = opportunity.budget_amount / target_min
            else:
                ratio = target_max / opportunity.budget_amount if target_max > 0 else 0.5
            score += max(0, ratio * 100) * w_budget
        total_weight += w_budget
    
    # Deadline urgency contribution
    if opportunity.deadline:
        days_until = (opportunity.deadline - date.today()).days
        if days_until <= 7:
            urgency_score = 100  # Urgent
        elif days_until <= 14:
            urgency_score = 80
        elif days_until <= 30:
            urgency_score = 60
        else:
            urgency_score = 40
        score += urgency_score * w_deadline
        total_weight += w_deadline
    
    # Category match
    if profile.criteria and 'categories' in profile.criteria:
        target_categories = profile.criteria.get('categories', [])
        if opportunity.category and opportunity.category in target_categories:
            score += 100 * w_category
        total_weight += w_category
    
    # Source preference
    if profile.criteria and 'preferred_sources' in profile.criteria:
        preferred = profile.criteria.get('preferred_sources', [])
        if opportunity.source_id and str(opportunity.source_id) in [str(s) for s in preferred]:
            score += 100 * w_source
        total_weight += w_source
    
    # Normalize
    if total_weight > 0:
        final_score = score / total_weight
    else:
        final_score = base_score
    
    return min(100, max(0, final_score))


def generate_shortlist_reasons(opportunity: Opportunity, fit_score: float, profile: Profile) -> List[Dict[str, Any]]:
    """Generate human-readable reasons for why an opportunity was selected."""
    reasons = []
    
    # Score-based reason
    if opportunity.score and opportunity.score >= 80:
        reasons.append({
            "emoji": "🎯",
            "label": "Score élevé",
            "value": f"{opportunity.score:.0f}%"
        })
    
    # Deadline urgency
    if opportunity.deadline_at:
        deadline_date = opportunity.deadline_at.date() if hasattr(opportunity.deadline_at, 'date') else opportunity.deadline_at
        days = (deadline_date - date.today()).days
        if days <= 3:
            reasons.append({
                "emoji": "⚡",
                "label": "Très urgent",
                "value": f"J-{days}"
            })
        elif days <= 7:
            reasons.append({
                "emoji": "⏰",
                "label": "Urgent",
                "value": f"J-{days}"
            })
    
    # Budget match
    if opportunity.budget_amount:
        reasons.append({
            "emoji": "💰",
            "label": "Budget",
            "value": f"{opportunity.budget_amount:,.0f}€"
        })
    
    # Fit score
    if fit_score >= 85:
        reasons.append({
            "emoji": "⭐",
            "label": "Excellent fit",
            "value": f"{fit_score:.0f}%"
        })
    elif fit_score >= 70:
        reasons.append({
            "emoji": "✅",
            "label": "Bon fit",
            "value": f"{fit_score:.0f}%"
        })
    
    return reasons


@celery_app.task(name="app.workers.radar_features_tasks.daily_shortlist_job")
def daily_shortlist_job(profile_id: Optional[int] = None):
    """
    Generate daily shortlist for all profiles (or specific profile).
    Runs at 08:00 Europe/Paris.
    """
    logger = get_task_logger("SHORTLIST")
    logger.info(f"🌅 Génération des shortlists quotidiennes...")
    
    db = get_db()
    try:
        # Get profiles to process
        if profile_id:
            profiles = db.query(Profile).filter(Profile.id == profile_id).all()
        else:
            profiles = db.query(Profile).filter(Profile.is_active == True).all()
        
        if not profiles:
            logger.warning("Aucun profil actif trouvé")
            return {"status": "no_profiles", "generated": 0}
        
        today = date.today()
        generated_count = 0
        
        for profile in profiles:
            logger.info(f"📊 Traitement profil: {profile.name}")
            
            # Get opportunities from last 7 days that are still active
            recent_opps = db.query(Opportunity).filter(
                Opportunity.status == OpportunityStatus.NEW,
                Opportunity.created_at >= datetime.now() - timedelta(days=7),
                or_(
                    Opportunity.deadline.is_(None),
                    Opportunity.deadline >= today
                )
            ).all()
            
            if not recent_opps:
                logger.info(f"  Aucune opportunité récente")
                continue
            
            # Calculate fit scores
            scored_opps = []
            for opp in recent_opps:
                fit_score = compute_fit_score(opp, profile)
                scored_opps.append((opp, fit_score))
            
            # Sort by fit score descending
            scored_opps.sort(key=lambda x: x[1], reverse=True)
            
            # Take top N (configurable, default 5)
            top_n = profile.criteria.get('shortlist_size', 5) if profile.criteria else 5
            top_opps = scored_opps[:top_n]
            
            # Build shortlist items
            items = []
            for opp, fit_score in top_opps:
                reasons = generate_shortlist_reasons(opp, fit_score, profile)
                items.append({
                    "opportunity_id": opp.id,
                    "fit_score": fit_score,
                    "reasons": reasons
                })
                
                # Update/create OpportunityProfileScore
                existing_score = db.query(OpportunityProfileScore).filter(
                    OpportunityProfileScore.opportunity_id == opp.id,
                    OpportunityProfileScore.profile_id == profile.id
                ).first()
                
                if existing_score:
                    existing_score.fit_score = fit_score
                    existing_score.computed_at = datetime.utcnow()
                else:
                    new_score = OpportunityProfileScore(
                        opportunity_id=opp.id,
                        profile_id=profile.id,
                        fit_score=fit_score
                    )
                    db.add(new_score)
            
            # Create shortlist record
            shortlist = DailyShortlist(
                date=today,
                profile_id=profile.id,
                items=items,
                count=len(items)
            )
            db.add(shortlist)
            generated_count += 1
            
            logger.success(f"  ✅ Shortlist générée: {len(items)} opportunités")
        
        db.commit()
        logger.success(f"🎉 {generated_count} shortlists générées")
        
        return {"status": "success", "generated": generated_count}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur génération shortlist: {e}")
        raise
    finally:
        db.close()


# ============================================================================
# CLUSTER REBUILD - Détection de doublons et regroupement
# ============================================================================

def normalize_url(url: str) -> str:
    """Normalize URL for comparison."""
    if not url:
        return ""
    url = url.lower().strip()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    url = re.sub(r'\?.*$', '', url)
    return url


def compute_text_similarity(text1: str, text2: str) -> float:
    """Simple text similarity using Jaccard index on words."""
    if not text1 or not text2:
        return 0.0
    
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def compute_opportunity_hash(opp: Opportunity) -> str:
    """Compute a hash for deduplication based on key fields."""
    content = f"{opp.title or ''}{opp.organization or ''}{opp.budget_amount or ''}"
    content = re.sub(r'\s+', '', content.lower())
    return hashlib.md5(content.encode()).hexdigest()[:16]


@celery_app.task(name="app.workers.radar_features_tasks.cluster_rebuild_job")
def cluster_rebuild_job():
    """
    Rebuild opportunity clusters based on similarity.
    Runs nightly.
    """
    logger = get_task_logger("CLUSTERS")
    logger.info(f"🔄 Reconstruction des clusters...")
    
    db = get_db()
    try:
        # Get active opportunities
        opportunities = db.query(Opportunity).filter(
            Opportunity.status.in_([OpportunityStatus.NEW, OpportunityStatus.CONTACTED])
        ).all()
        
        if not opportunities:
            logger.info("Aucune opportunité à clusteriser")
            return {"status": "no_opportunities", "clusters": 0}
        
        logger.info(f"📊 Analyse de {len(opportunities)} opportunités")
        
        # Build URL-based clusters first
        url_clusters = defaultdict(list)
        for opp in opportunities:
            if opp.source_url:
                normalized = normalize_url(opp.source_url)
                url_clusters[normalized].append(opp)
        
        # Build hash-based clusters
        hash_clusters = defaultdict(list)
        for opp in opportunities:
            opp_hash = compute_opportunity_hash(opp)
            hash_clusters[opp_hash].append(opp)
        
        # Merge clusters
        processed_ids = set()
        clusters_created = 0
        duplicates_found = 0
        
        # Clear existing clusters
        db.query(OpportunityClusterMember).delete()
        db.query(OpportunityCluster).delete()
        
        # Process URL clusters
        for url, opps in url_clusters.items():
            if len(opps) > 1:
                ids_in_cluster = [o.id for o in opps]
                if any(oid in processed_ids for oid in ids_in_cluster):
                    continue
                
                # Create cluster
                canonical = max(opps, key=lambda o: o.score or 0)
                cluster = OpportunityCluster(
                    canonical_id=canonical.id,
                    match_type="url",
                    confidence=0.95
                )
                db.add(cluster)
                db.flush()
                
                for opp in opps:
                    member = OpportunityClusterMember(
                        cluster_id=cluster.id,
                        opportunity_id=opp.id,
                        is_canonical=(opp.id == canonical.id)
                    )
                    db.add(member)
                    processed_ids.add(opp.id)
                
                clusters_created += 1
                duplicates_found += len(opps) - 1
        
        # Process hash clusters
        for h, opps in hash_clusters.items():
            if len(opps) > 1:
                ids_in_cluster = [o.id for o in opps]
                if any(oid in processed_ids for oid in ids_in_cluster):
                    continue
                
                canonical = max(opps, key=lambda o: o.score or 0)
                cluster = OpportunityCluster(
                    canonical_id=canonical.id,
                    match_type="hash",
                    confidence=0.85
                )
                db.add(cluster)
                db.flush()
                
                for opp in opps:
                    member = OpportunityClusterMember(
                        cluster_id=cluster.id,
                        opportunity_id=opp.id,
                        is_canonical=(opp.id == canonical.id)
                    )
                    db.add(member)
                    processed_ids.add(opp.id)
                
                clusters_created += 1
                duplicates_found += len(opps) - 1
        
        # Find text-similar opportunities
        unprocessed = [o for o in opportunities if o.id not in processed_ids]
        for i, opp1 in enumerate(unprocessed):
            if opp1.id in processed_ids:
                continue
            
            similar = [opp1]
            for opp2 in unprocessed[i+1:]:
                if opp2.id in processed_ids:
                    continue
                
                # Check title similarity
                sim = compute_text_similarity(opp1.title or '', opp2.title or '')
                if sim >= 0.7:
                    similar.append(opp2)
            
            if len(similar) > 1:
                canonical = max(similar, key=lambda o: o.score or 0)
                cluster = OpportunityCluster(
                    canonical_id=canonical.id,
                    match_type="text",
                    confidence=0.7
                )
                db.add(cluster)
                db.flush()
                
                for opp in similar:
                    member = OpportunityClusterMember(
                        cluster_id=cluster.id,
                        opportunity_id=opp.id,
                        is_canonical=(opp.id == canonical.id)
                    )
                    db.add(member)
                    processed_ids.add(opp.id)
                
                clusters_created += 1
                duplicates_found += len(similar) - 1
        
        db.commit()
        
        logger.success(f"✅ {clusters_created} clusters créés, {duplicates_found} doublons détectés")
        
        return {
            "status": "success",
            "clusters_created": clusters_created,
            "duplicates_found": duplicates_found,
            "opportunities_processed": len(opportunities)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur reconstruction clusters: {e}")
        raise
    finally:
        db.close()


# ============================================================================
# DEADLINE GUARD - Alertes sur les deadlines
# ============================================================================

@celery_app.task(name="app.workers.radar_features_tasks.deadline_guard_job")
def deadline_guard_job():
    """
    Create deadline alerts for opportunities with upcoming deadlines.
    Runs daily.
    """
    logger = get_task_logger("DEADLINES")
    logger.info(f"⏰ Vérification des deadlines...")
    
    db = get_db()
    try:
        today = date.today()
        alert_days = [7, 3, 1]  # J-7, J-3, J-1
        
        opportunities = db.query(Opportunity).filter(
            Opportunity.deadline.isnot(None),
            Opportunity.deadline >= today,
            Opportunity.status == OpportunityStatus.NEW
        ).all()
        
        if not opportunities:
            logger.info("Aucune opportunité avec deadline")
            return {"status": "no_deadlines", "alerts_created": 0}
        
        logger.info(f"📊 Vérification de {len(opportunities)} opportunités")
        
        alerts_created = 0
        
        for opp in opportunities:
            days_until = (opp.deadline - today).days
            
            for alert_day in alert_days:
                if days_until == alert_day:
                    # Check if alert already exists
                    existing = db.query(DeadlineAlert).filter(
                        DeadlineAlert.opportunity_id == opp.id,
                        DeadlineAlert.alert_type == AlertType(f"J_{alert_day}")
                    ).first()
                    
                    if not existing:
                        alert_type = AlertType.J_7 if alert_day == 7 else (
                            AlertType.J_3 if alert_day == 3 else AlertType.J_1
                        )
                        
                        alert = DeadlineAlert(
                            opportunity_id=opp.id,
                            deadline=opp.deadline,
                            alert_type=alert_type,
                            status=AlertStatus.PENDING,
                            scheduled_at=datetime.utcnow()
                        )
                        db.add(alert)
                        alerts_created += 1
                        
                        logger.info(f"  📌 Alerte J-{alert_day}: {opp.title[:50]}...")
        
        db.commit()
        logger.success(f"✅ {alerts_created} alertes créées")
        
        return {"status": "success", "alerts_created": alerts_created}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur deadline guard: {e}")
        raise
    finally:
        db.close()


# ============================================================================
# SOURCE HEALTH - Suivi de la santé des sources
# ============================================================================

@celery_app.task(name="app.workers.radar_features_tasks.source_health_rollup_job")
def source_health_rollup_job():
    """
    Calculate daily health metrics for all sources.
    Runs daily at 01:00.
    """
    logger = get_task_logger("HEALTH")
    logger.info(f"🏥 Calcul de la santé des sources...")
    
    db = get_db()
    try:
        sources = db.query(SourceConfig).filter(SourceConfig.is_active == True).all()
        
        if not sources:
            logger.info("Aucune source active")
            return {"status": "no_sources", "processed": 0}
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        processed = 0
        
        for source in sources:
            # Get opportunities ingested yesterday
            opps_count = db.query(func.count(Opportunity.id)).filter(
                Opportunity.source_id == source.id,
                func.date(Opportunity.created_at) == yesterday
            ).scalar() or 0
            
            # Get average score of opportunities
            avg_score = db.query(func.avg(Opportunity.score)).filter(
                Opportunity.source_id == source.id,
                func.date(Opportunity.created_at) == yesterday
            ).scalar() or 0.0
            
            # Calculate duplicates (opportunities in clusters)
            duplicates = db.query(func.count(OpportunityClusterMember.id)).join(
                Opportunity,
                OpportunityClusterMember.opportunity_id == Opportunity.id
            ).filter(
                Opportunity.source_id == source.id,
                func.date(Opportunity.created_at) == yesterday
            ).scalar() or 0
            
            # Error rate (simplified - based on ingestion runs)
            from app.db.models.ingestion import IngestionRun, IngestionStatus
            
            runs = db.query(IngestionRun).filter(
                IngestionRun.source_id == source.id,
                func.date(IngestionRun.started_at) == yesterday
            ).all()
            
            error_count = sum(1 for r in runs if r.status == IngestionStatus.FAILED)
            total_runs = len(runs)
            error_rate = (error_count / total_runs * 100) if total_runs > 0 else 0.0
            
            # Freshness (hours since last opportunity)
            last_opp = db.query(Opportunity).filter(
                Opportunity.source_id == source.id
            ).order_by(desc(Opportunity.created_at)).first()
            
            if last_opp:
                hours_since = (datetime.utcnow() - last_opp.created_at).total_seconds() / 3600
            else:
                hours_since = 999.0
            
            # Calculate overall health score
            health_score = 100.0
            health_score -= min(50, error_rate)  # Up to 50 points for errors
            if hours_since > 48:
                health_score -= 20  # Stale source
            elif hours_since > 24:
                health_score -= 10
            if avg_score < 50:
                health_score -= 10
            health_score = max(0, health_score)
            
            # Create health record
            health = SourceHealth(
                source_id=source.id,
                date=yesterday,
                opportunities_found=opps_count,
                duplicates_found=duplicates,
                avg_score=avg_score,
                error_rate=error_rate,
                freshness_hours=hours_since,
                health_score=health_score
            )
            db.add(health)
            processed += 1
            
            # Log status
            status = "🟢" if health_score >= 80 else ("🟡" if health_score >= 50 else "🔴")
            logger.info(f"  {status} {source.name}: {health_score:.0f}%")
        
        db.commit()
        logger.success(f"✅ {processed} sources analysées")
        
        return {"status": "success", "processed": processed}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur health rollup: {e}")
        raise
    finally:
        db.close()


# ============================================================================
# CONTACT FINDER - Recherche de contacts (on-demand)
# ============================================================================

@celery_app.task(name="app.workers.radar_features_tasks.contact_finder_job")
def contact_finder_job(opportunity_id: int, user_id: int):
    """
    Find contact information for an opportunity.
    Triggered on-demand when user requests it.
    """
    logger = get_task_logger("CONTACT")
    logger.info(f"🔍 Recherche contacts pour opportunité #{opportunity_id}...")
    
    db = get_db()
    try:
        opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        
        if not opp:
            logger.error(f"Opportunité #{opportunity_id} non trouvée")
            return {"status": "not_found", "opportunity_id": opportunity_id}
        
        # Check if we already have a result
        existing = db.query(ContactFinderResult).filter(
            ContactFinderResult.opportunity_id == opportunity_id
        ).first()
        
        if existing and existing.status == "completed":
            logger.info(f"Résultat existant trouvé")
            return {
                "status": "cached",
                "opportunity_id": opportunity_id,
                "contacts": existing.contacts
            }
        
        # Extract potential contacts from opportunity data
        contacts = []
        evidence = []
        
        # 1. Check if organization website exists
        org_name = opp.organization
        if org_name:
            # Simplified: would use web scraping in production
            evidence.append(f"Organisation: {org_name}")
        
        # 2. Extract emails from description
        if opp.description:
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, opp.description)
            for email in emails:
                contacts.append({
                    "type": "email",
                    "value": email,
                    "confidence": 0.9,
                    "source": "description"
                })
                evidence.append(f"Email trouvé dans description: {email}")
        
        # 3. Extract phone numbers
        if opp.description:
            phone_pattern = r'(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}'
            phones = re.findall(phone_pattern, opp.description)
            for phone in phones:
                normalized = re.sub(r'\s+', '', phone)
                contacts.append({
                    "type": "phone",
                    "value": normalized,
                    "confidence": 0.85,
                    "source": "description"
                })
                evidence.append(f"Téléphone trouvé: {normalized}")
        
        # 4. Check source URL for contact page (simplified)
        if opp.source_url:
            evidence.append(f"Source: {opp.source_url}")
        
        # Save result
        if existing:
            existing.contacts = contacts
            existing.evidence = evidence
            existing.status = "completed"
            existing.completed_at = datetime.utcnow()
        else:
            result = ContactFinderResult(
                opportunity_id=opportunity_id,
                requested_by=user_id,
                contacts=contacts,
                evidence=evidence,
                status="completed",
                completed_at=datetime.utcnow()
            )
            db.add(result)
        
        db.commit()
        
        logger.success(f"✅ {len(contacts)} contacts trouvés")
        
        return {
            "status": "success",
            "opportunity_id": opportunity_id,
            "contacts": contacts,
            "evidence": evidence
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur contact finder: {e}")
        raise
    finally:
        db.close()
