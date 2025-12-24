"""
Deduplicator - Detect and handle duplicate opportunities
"""
import hashlib
from typing import Optional, Tuple, List
from datetime import datetime, timedelta

from unidecode import unidecode
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models.opportunity import Opportunity


class Deduplicator:
    """Handle deduplication of opportunities"""
    
    # Similarity threshold for text comparison (0-1)
    SIMILARITY_THRESHOLD = 0.7
    
    def __init__(self, db: Session):
        self.db = db
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        if not title:
            return ""
        # Remove accents, lowercase, remove special chars
        text = unidecode(title.lower())
        text = ''.join(c for c in text if c.isalnum() or c.isspace())
        text = ' '.join(text.split())
        return text
    
    def compute_hash(self, title: str, organization: str = None, 
                     deadline: datetime = None, source_name: str = None) -> str:
        """Compute hash for deduplication"""
        normalized_title = self.normalize_title(title)
        
        # Approximate deadline to week
        deadline_approx = ""
        if deadline:
            # Round to start of week
            week_start = deadline - timedelta(days=deadline.weekday())
            deadline_approx = week_start.strftime("%Y-W%W")
        
        org = self.normalize_title(organization or "")
        
        components = f"{normalized_title}|{org}|{deadline_approx}|{source_name or ''}"
        return hashlib.sha256(components.encode()).hexdigest()[:32]
    
    def jaccard_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Tokenize
        words1 = set(self.normalize_title(text1).split())
        words2 = set(self.normalize_title(text2).split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard index
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def find_by_external_id(self, external_id: str) -> Optional[Opportunity]:
        """Find opportunity by external ID"""
        return self.db.query(Opportunity).filter(
            Opportunity.external_id == external_id
        ).first()
    
    def find_by_url(self, url: str) -> Optional[Opportunity]:
        """Find opportunity by primary URL"""
        if not url:
            return None
        return self.db.query(Opportunity).filter(
            Opportunity.url_primary == url
        ).first()
    
    def find_similar(self, title: str, organization: str = None,
                     deadline: datetime = None, limit: int = 5) -> List[Tuple[Opportunity, float]]:
        """
        Find potentially similar opportunities.
        Returns list of (opportunity, similarity_score) tuples.
        """
        similar = []
        normalized_title = self.normalize_title(title)
        
        if len(normalized_title) < 10:
            return similar
        
        # Search by partial title match
        # Use first significant words for query
        search_words = normalized_title.split()[:3]
        search_pattern = '%' + '%'.join(search_words) + '%'
        
        candidates = self.db.query(Opportunity).filter(
            Opportunity.title.ilike(search_pattern)
        ).limit(limit * 2).all()
        
        # Also search by organization if provided
        if organization:
            org_candidates = self.db.query(Opportunity).filter(
                Opportunity.organization.ilike(f"%{organization}%")
            ).limit(limit).all()
            candidates.extend(org_candidates)
        
        # Compute similarity for each
        seen_ids = set()
        for opp in candidates:
            if opp.id in seen_ids:
                continue
            seen_ids.add(opp.id)
            
            # Combine title and organization for comparison
            text1 = f"{title} {organization or ''}"
            text2 = f"{opp.title} {opp.organization or ''}"
            
            similarity = self.jaccard_similarity(text1, text2)
            
            # Boost similarity if deadlines are close
            if deadline and opp.deadline_at:
                days_diff = abs((deadline - opp.deadline_at).days)
                if days_diff <= 7:
                    similarity = min(1.0, similarity + 0.1)
            
            if similarity >= self.SIMILARITY_THRESHOLD:
                similar.append((opp, similarity))
        
        # Sort by similarity
        similar.sort(key=lambda x: x[1], reverse=True)
        
        return similar[:limit]
    
    def check_duplicate(self, external_id: str, url: str = None,
                        title: str = None, organization: str = None,
                        deadline: datetime = None) -> Tuple[bool, Optional[Opportunity], Optional[float]]:
        """
        Check if an opportunity is a duplicate.
        Returns (is_duplicate, existing_opportunity, similarity_score)
        """
        # Check by external ID first (exact match)
        existing = self.find_by_external_id(external_id)
        if existing:
            return True, existing, 1.0
        
        # Check by URL
        if url:
            existing = self.find_by_url(url)
            if existing:
                return True, existing, 1.0
        
        # Check by similarity (possible duplicate)
        if title:
            similar = self.find_similar(title, organization, deadline, limit=1)
            if similar:
                opp, score = similar[0]
                if score >= 0.9:
                    # Very high similarity, consider duplicate
                    return True, opp, score
                elif score >= self.SIMILARITY_THRESHOLD:
                    # Possible duplicate, flag it
                    return False, opp, score
        
        return False, None, None
    
    def mark_possible_duplicate(self, opportunity: Opportunity, 
                                similar_to: Opportunity, similarity: float):
        """Mark an opportunity as possible duplicate"""
        opportunity.possible_duplicate = True
        if not opportunity.score_breakdown:
            opportunity.score_breakdown = {}
        opportunity.score_breakdown['possible_duplicate_of'] = str(similar_to.id)
        opportunity.score_breakdown['duplicate_similarity'] = round(similarity, 2)
