"""
Clusters API - Intelligent Deduplication
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
import time
import hashlib
import re

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.db.models import Opportunity, OpportunityCluster, OpportunityClusterMember
from app.api.deps import get_current_user, get_current_admin_user
from app.schemas.radar_features import (
    ClusterResponse,
    ClusterMember,
    ClusterRebuildResponse,
)

router = APIRouter(prefix="/clusters", tags=["clusters"])


def normalize_url(url: str) -> str:
    """Normalize URL for comparison"""
    if not url:
        return ""
    # Remove protocol, www, trailing slashes, query params
    url = url.lower()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    url = url.split('?')[0]
    return url


def compute_opportunity_hash(opportunity: Opportunity) -> str:
    """Compute a hash for deduplication based on key fields"""
    # Normalize fields
    title = (opportunity.title or "").lower().strip()
    org = (opportunity.organization or "").lower().strip()
    city = (opportunity.location_city or "").lower().strip()
    
    # Remove common words
    for word in ["appel", "offre", "marché", "projet", "the", "de", "du", "la", "le"]:
        title = title.replace(word, "")
    
    # Create hash from normalized data
    combined = f"{title}|{org}|{city}"
    combined = re.sub(r'\s+', '', combined)  # Remove all whitespace
    
    return hashlib.md5(combined.encode()).hexdigest()[:16]


def compute_text_similarity(text1: str, text2: str) -> float:
    """
    Compute simple text similarity using word overlap (Jaccard similarity).
    For production, consider TF-IDF cosine similarity.
    """
    if not text1 or not text2:
        return 0.0
    
    # Tokenize
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


@router.get("/opportunity/{opportunity_id}", response_model=Optional[ClusterResponse])
def get_opportunity_cluster(
    opportunity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get cluster information for an opportunity"""
    # Check if opportunity is a canonical in a cluster
    cluster = db.query(OpportunityCluster).filter(
        OpportunityCluster.canonical_opportunity_id == opportunity_id
    ).first()
    
    # If not canonical, check if it's a member
    if not cluster:
        member = db.query(OpportunityClusterMember).filter(
            OpportunityClusterMember.opportunity_id == opportunity_id
        ).first()
        if member:
            cluster = member.cluster
    
    if not cluster:
        return None
    
    # Get canonical opportunity
    canonical = db.query(Opportunity).filter(
        Opportunity.id == cluster.canonical_opportunity_id
    ).first()
    
    # Get all members
    members = db.query(OpportunityClusterMember).filter(
        OpportunityClusterMember.cluster_id == cluster.id
    ).all()
    
    member_list = []
    for m in members:
        opp = db.query(Opportunity).filter(Opportunity.id == m.opportunity_id).first()
        if opp:
            member_list.append(ClusterMember(
                opportunity_id=opp.id,
                title=opp.title,
                source_name=opp.source_name,
                url=opp.url_primary,
                similarity_score=m.similarity_score,
                match_type=m.match_type,
            ))
    
    return ClusterResponse(
        cluster_id=cluster.id,
        canonical_opportunity_id=cluster.canonical_opportunity_id,
        canonical_title=canonical.title if canonical else "Unknown",
        member_count=cluster.member_count,
        cluster_score=cluster.cluster_score,
        members=member_list,
    )


@router.post("/rebuild", response_model=ClusterRebuildResponse)
def rebuild_clusters(
    batch_size: int = Query(default=1000, ge=100, le=5000),
    similarity_threshold: float = Query(default=0.86, ge=0.5, le=1.0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
):
    """
    Rebuild all opportunity clusters.
    This is a resource-intensive operation.
    """
    start_time = time.time()
    
    # Clear existing clusters
    db.query(OpportunityClusterMember).delete()
    db.query(OpportunityCluster).delete()
    db.commit()
    
    # Get all active opportunities
    opportunities = db.query(Opportunity).filter(
        Opportunity.status.notin_(["ARCHIVED"])
    ).order_by(Opportunity.created_at.desc()).limit(batch_size).all()
    
    # Build hash index
    hash_index = {}  # hash -> list of opportunities
    url_index = {}   # normalized_url -> list of opportunities
    
    for opp in opportunities:
        # URL indexing
        if opp.url_primary:
            norm_url = normalize_url(opp.url_primary)
            if norm_url:
                if norm_url not in url_index:
                    url_index[norm_url] = []
                url_index[norm_url].append(opp)
        
        # Hash indexing
        opp_hash = compute_opportunity_hash(opp)
        if opp_hash not in hash_index:
            hash_index[opp_hash] = []
        hash_index[opp_hash].append(opp)
    
    clusters_created = 0
    opportunities_clustered = 0
    processed_ids = set()
    
    # Create clusters from URL matches
    for norm_url, opps in url_index.items():
        if len(opps) > 1:
            # Sort by score to pick canonical
            opps.sort(key=lambda o: o.score or 0, reverse=True)
            canonical = opps[0]
            
            if canonical.id in processed_ids:
                continue
            
            # Create cluster
            cluster = OpportunityCluster(
                canonical_opportunity_id=canonical.id,
                cluster_score=1.0,
                member_count=len(opps),
            )
            db.add(cluster)
            db.flush()
            
            # Add members
            for opp in opps:
                if opp.id not in processed_ids:
                    member = OpportunityClusterMember(
                        cluster_id=cluster.id,
                        opportunity_id=opp.id,
                        similarity_score=1.0,
                        match_type="url",
                    )
                    db.add(member)
                    processed_ids.add(opp.id)
                    opportunities_clustered += 1
            
            clusters_created += 1
    
    # Create clusters from hash matches
    for opp_hash, opps in hash_index.items():
        if len(opps) > 1:
            # Filter already processed
            opps = [o for o in opps if o.id not in processed_ids]
            if len(opps) < 2:
                continue
            
            # Sort by score
            opps.sort(key=lambda o: o.score or 0, reverse=True)
            canonical = opps[0]
            
            # Create cluster
            cluster = OpportunityCluster(
                canonical_opportunity_id=canonical.id,
                cluster_score=0.95,
                member_count=len(opps),
            )
            db.add(cluster)
            db.flush()
            
            # Add members
            for opp in opps:
                member = OpportunityClusterMember(
                    cluster_id=cluster.id,
                    opportunity_id=opp.id,
                    similarity_score=0.95,
                    match_type="hash",
                )
                db.add(member)
                processed_ids.add(opp.id)
                opportunities_clustered += 1
            
            clusters_created += 1
    
    # Text similarity matching (more expensive)
    remaining = [o for o in opportunities if o.id not in processed_ids]
    
    for i, opp1 in enumerate(remaining):
        if opp1.id in processed_ids:
            continue
        
        similar_opps = [opp1]
        
        for opp2 in remaining[i+1:]:
            if opp2.id in processed_ids:
                continue
            
            # Compute similarity
            text1 = f"{opp1.title} {opp1.snippet or ''}"
            text2 = f"{opp2.title} {opp2.snippet or ''}"
            
            similarity = compute_text_similarity(text1, text2)
            
            if similarity >= similarity_threshold:
                similar_opps.append(opp2)
        
        if len(similar_opps) > 1:
            # Sort by score
            similar_opps.sort(key=lambda o: o.score or 0, reverse=True)
            canonical = similar_opps[0]
            
            # Create cluster
            cluster = OpportunityCluster(
                canonical_opportunity_id=canonical.id,
                cluster_score=similarity_threshold,
                member_count=len(similar_opps),
            )
            db.add(cluster)
            db.flush()
            
            # Add members
            for opp in similar_opps:
                member = OpportunityClusterMember(
                    cluster_id=cluster.id,
                    opportunity_id=opp.id,
                    similarity_score=similarity_threshold,
                    match_type="cosine",
                )
                db.add(member)
                processed_ids.add(opp.id)
                opportunities_clustered += 1
            
            clusters_created += 1
    
    db.commit()
    
    duration = time.time() - start_time
    
    return ClusterRebuildResponse(
        clusters_created=clusters_created,
        clusters_updated=0,
        opportunities_clustered=opportunities_clustered,
        duration_seconds=round(duration, 2),
    )


@router.get("/stats")
def get_cluster_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get cluster statistics"""
    total_clusters = db.query(func.count(OpportunityCluster.id)).scalar()
    total_members = db.query(func.count(OpportunityClusterMember.id)).scalar()
    
    # Average members per cluster
    avg_members = db.query(func.avg(OpportunityCluster.member_count)).scalar() or 0
    
    # Clusters by match type
    match_type_stats = db.query(
        OpportunityClusterMember.match_type,
        func.count(OpportunityClusterMember.id)
    ).group_by(OpportunityClusterMember.match_type).all()
    
    return {
        "total_clusters": total_clusters,
        "total_clustered_opportunities": total_members,
        "avg_members_per_cluster": round(avg_members, 2),
        "by_match_type": {mt: count for mt, count in match_type_stats}
    }
