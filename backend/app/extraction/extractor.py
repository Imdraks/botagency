"""
Data extractor - Extract structured data from raw content
"""
import re
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
from decimal import Decimal
from dateutil import parser as date_parser
from unidecode import unidecode

from app.db.models.opportunity import OpportunityCategory


class DataExtractor:
    """Extract structured data from raw content"""
    
    # French date patterns
    DATE_PATTERNS = [
        # DD/MM/YYYY or DD-MM-YYYY
        r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
        # DD month YYYY (French)
        r'(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(\d{4})',
        # "avant le", "date limite", "deadline"
        r'(?:avant le|date limite|deadline|échéance|echeance)[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
        r'(?:avant le|date limite|deadline|échéance|echeance)[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
    ]
    
    MONTH_NAMES_FR = {
        'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
    }
    
    # Budget patterns
    BUDGET_PATTERNS = [
        # 10 000 € or 10000€
        r'(\d[\d\s]*(?:[,\.]\d+)?)\s*(?:€|euros?|EUR)',
        # budget: X € 
        r'(?:budget|montant|enveloppe|valeur)[:\s]+(\d[\d\s]*(?:[,\.]\d+)?)\s*(?:€|euros?|EUR)?',
        # X € HT or X € TTC
        r'(\d[\d\s]*(?:[,\.]\d+)?)\s*(?:€|euros?)\s*(?:HT|TTC)',
    ]
    
    # Contact patterns
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    PHONE_PATTERN = r'(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}'
    
    # Category keywords
    CATEGORY_KEYWORDS = {
        OpportunityCategory.PUBLIC_TENDER: [
            'marché public', 'appel d\'offres', 'consultation', 'dce',
            'cahier des charges', 'mapa', 'avis de marché', 'marchés publics',
            'procédure adaptée', 'appel à candidature'
        ],
        OpportunityCategory.CALL_FOR_PROJECTS: [
            'appel à projets', 'appel à projet', 'ami', 'appel à manifestation',
            'appel à candidatures', 'candidature', 'sélection de projets'
        ],
        OpportunityCategory.GRANT: [
            'subvention', 'aide', 'financement', 'dotation', 'bourse',
            'soutien financier', 'contribution', 'mécénat'
        ],
        OpportunityCategory.PARTNERSHIP: [
            'partenariat', 'sponsor', 'sponsoring', 'partenaire',
            'brand content', 'collaboration', 'co-branding', 'naming'
        ],
        OpportunityCategory.VENUE: [
            'privatisation', 'lieu', 'location de salle', 'espace événementiel',
            'réception', 'salle de réception', 'domaine', 'château',
            'location événementielle', 'surface événementielle'
        ],
        OpportunityCategory.SUPPLIER: [
            'prestataire', 'technique', 'régie', 'scénographie',
            'production événement', 'traiteur', 'décoration', 'sonorisation',
            'éclairage', 'audiovisuel', 'captation', 'streaming'
        ],
    }
    
    # Region detection (French regions)
    REGIONS = {
        'ile-de-france': ['paris', 'ile-de-france', 'idf', '75', '77', '78', '91', '92', '93', '94', '95'],
        'auvergne-rhone-alpes': ['lyon', 'grenoble', 'saint-etienne', 'auvergne', 'rhone-alpes', 'rhône-alpes'],
        'nouvelle-aquitaine': ['bordeaux', 'limoges', 'poitiers', 'nouvelle-aquitaine', 'aquitaine'],
        'occitanie': ['toulouse', 'montpellier', 'occitanie', 'midi-pyrénées', 'languedoc'],
        'provence-alpes-cote-d-azur': ['marseille', 'nice', 'toulon', 'paca', 'provence', 'côte d\'azur'],
        'hauts-de-france': ['lille', 'amiens', 'hauts-de-france', 'nord-pas-de-calais', 'picardie'],
        'grand-est': ['strasbourg', 'reims', 'metz', 'nancy', 'grand-est', 'alsace', 'lorraine'],
        'pays-de-la-loire': ['nantes', 'angers', 'le mans', 'pays-de-la-loire', 'pays de la loire'],
        'bretagne': ['rennes', 'brest', 'bretagne'],
        'normandie': ['rouen', 'caen', 'le havre', 'normandie'],
        'bourgogne-franche-comte': ['dijon', 'besançon', 'bourgogne', 'franche-comté'],
        'centre-val-de-loire': ['orléans', 'tours', 'centre', 'val de loire'],
        'corse': ['ajaccio', 'bastia', 'corse'],
    }
    
    def __init__(self):
        pass
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        text = unidecode(text.lower())
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_deadline(self, text: str) -> Optional[datetime]:
        """Extract deadline date from text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Try specific deadline patterns first
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    
                    # Handle different formats
                    if len(groups) == 3:
                        if groups[1].isdigit():
                            # DD/MM/YYYY
                            day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        else:
                            # DD month YYYY
                            day = int(groups[0])
                            month = self.MONTH_NAMES_FR.get(groups[1].lower(), 1)
                            year = int(groups[2])
                        
                        return datetime(year, month, day)
                    elif len(groups) == 1:
                        # Extracted date string, parse it
                        return date_parser.parse(groups[0], dayfirst=True)
                        
                except (ValueError, TypeError):
                    continue
        
        # Fallback: try dateutil parser
        try:
            # Look for date-like strings
            date_match = re.search(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', text)
            if date_match:
                return date_parser.parse(date_match.group(), dayfirst=True)
        except:
            pass
        
        return None
    
    def extract_budget(self, text: str) -> Tuple[Optional[Decimal], Optional[str]]:
        """
        Extract budget from text.
        Returns (budget_amount, budget_hint)
        """
        if not text:
            return None, None
        
        budget_hint = None
        budget_amount = None
        
        for pattern in self.BUDGET_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value_str = match.group(1)
                    # Clean the value
                    value_str = re.sub(r'\s', '', value_str)
                    value_str = value_str.replace(',', '.')
                    
                    # Handle multiple decimal points
                    parts = value_str.split('.')
                    if len(parts) > 2:
                        value_str = ''.join(parts[:-1]) + '.' + parts[-1]
                    
                    budget_amount = Decimal(value_str)
                    budget_hint = match.group(0).strip()
                    break
                except (ValueError, TypeError):
                    budget_hint = match.group(0).strip()
                    continue
        
        # If no amount found but budget-related words exist, capture as hint
        if not budget_hint:
            budget_keywords = ['budget', 'montant', 'enveloppe', 'valeur', '€', 'euros']
            for keyword in budget_keywords:
                if keyword in text.lower():
                    # Extract surrounding context
                    match = re.search(rf'.{{0,30}}{keyword}.{{0,50}}', text, re.IGNORECASE)
                    if match:
                        budget_hint = match.group(0).strip()
                        break
        
        return budget_amount, budget_hint
    
    def extract_contacts(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract contact information from text.
        Returns (email, phone, contact_url)
        """
        if not text:
            return None, None, None
        
        # Extract email
        email_match = re.search(self.EMAIL_PATTERN, text)
        email = email_match.group(0) if email_match else None
        
        # Extract phone
        phone_match = re.search(self.PHONE_PATTERN, text)
        phone = phone_match.group(0) if phone_match else None
        if phone:
            # Normalize phone format
            phone = re.sub(r'[\s.-]', '', phone)
        
        # Look for contact URL
        contact_url = None
        contact_patterns = [
            r'https?://[^\s<>"]*contact[^\s<>"]*',
            r'https?://[^\s<>"]*nous-joindre[^\s<>"]*',
        ]
        for pattern in contact_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                contact_url = match.group(0)
                break
        
        return email, phone, contact_url
    
    def detect_category(self, text: str, title: str = "") -> OpportunityCategory:
        """Detect opportunity category from content"""
        combined = f"{title} {text}".lower()
        normalized = self.normalize_text(combined)
        
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined or self.normalize_text(kw) in normalized)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return OpportunityCategory.OTHER
    
    def detect_region(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect location from text.
        Returns (city, region)
        """
        if not text:
            return None, None
        
        text_lower = text.lower()
        normalized = self.normalize_text(text)
        
        for region, keywords in self.REGIONS.items():
            for keyword in keywords:
                if keyword in text_lower or keyword in normalized:
                    # Return first matching city and region
                    city = keyword if len(keyword) > 3 and not keyword.isdigit() else None
                    return city, region.replace('-', ' ').title()
        
        return None, None
    
    def detect_organization(self, text: str) -> Optional[str]:
        """Try to detect organization name from text"""
        if not text:
            return None
        
        # Common patterns
        patterns = [
            r'(?:organisé par|proposé par|porté par|émis par|lancé par)[:\s]+([^,.\n]+)',
            r'(?:mairie de|ville de|région|département|communauté)[:\s]+([^,.\n]+)',
            r'(?:ministère|préfecture|conseil)[:\s]+([^,.\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                org = match.group(1).strip()
                if len(org) > 3 and len(org) < 100:
                    return org
        
        return None
    
    def generate_external_id(self, source_type: str, source_name: str, 
                             url: Optional[str] = None, message_id: Optional[str] = None,
                             title: Optional[str] = None) -> str:
        """Generate stable external ID for deduplication"""
        if message_id:
            base = f"{source_type}:{source_name}:{message_id}"
        elif url:
            base = f"{source_type}:{source_name}:{url}"
        else:
            base = f"{source_type}:{source_name}:{self.normalize_text(title or '')}"
        
        return hashlib.sha256(base.encode()).hexdigest()[:32]
    
    def create_snippet(self, text: str, max_length: int = 500) -> str:
        """Create a snippet from text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= max_length:
            return text
        
        # Try to break at sentence boundary
        snippet = text[:max_length]
        last_period = snippet.rfind('.')
        if last_period > max_length * 0.5:
            return snippet[:last_period + 1]
        
        # Break at word boundary
        last_space = snippet.rfind(' ')
        if last_space > 0:
            return snippet[:last_space] + '...'
        
        return snippet + '...'
    
    def extract_all(self, raw_item: Dict[str, Any], source_type: str, source_name: str) -> Dict[str, Any]:
        """
        Extract all structured data from a raw item.
        Returns a dictionary ready for Opportunity model.
        """
        content = raw_item.get('content', '') or ''
        title = raw_item.get('title', '') or 'Sans titre'
        
        # Combine for extraction
        full_text = f"{title}\n{content}"
        
        # Extract deadline
        deadline_text = raw_item.get('deadline_text', '')
        deadline = self.extract_deadline(deadline_text) or self.extract_deadline(full_text)
        
        # Extract budget
        budget_text = raw_item.get('budget_text', '')
        budget_amount, budget_hint = self.extract_budget(budget_text) or self.extract_budget(full_text)
        if not budget_amount and not budget_hint:
            budget_amount, budget_hint = self.extract_budget(full_text)
        
        # Extract contacts
        contact_email, contact_phone, contact_url = self.extract_contacts(full_text)
        
        # Detect category
        category = self.detect_category(content, title)
        
        # Detect location
        location_text = raw_item.get('location', '') or ''
        city, region = self.detect_region(f"{location_text} {full_text}")
        
        # Detect organization
        org = raw_item.get('organization') or self.detect_organization(full_text)
        
        # URLs
        primary_link = raw_item.get('primary_link')
        links = raw_item.get('links', [])
        if primary_link and primary_link not in links:
            links = [primary_link] + links
        
        # Generate external ID
        external_id = self.generate_external_id(
            source_type=source_type,
            source_name=source_name,
            url=primary_link,
            message_id=raw_item.get('message_id') or raw_item.get('item_id') or raw_item.get('entry_id'),
            title=title
        )
        
        # Create snippet
        snippet = self.create_snippet(content)
        
        # Published date
        published_at = raw_item.get('published_at')
        if isinstance(published_at, str):
            try:
                published_at = date_parser.parse(published_at)
            except:
                published_at = None
        
        return {
            'external_id': external_id,
            'source_type': source_type,
            'source_name': source_name,
            'title': title[:500],
            'category': category,
            'organization': org[:255] if org else None,
            'description': content,
            'snippet': snippet,
            'url_primary': primary_link,
            'urls_all': links[:20],  # Limit to 20 URLs
            'published_at': published_at,
            'deadline_at': deadline,
            'location_city': city[:100] if city else None,
            'location_region': region[:100] if region else None,
            'budget_amount': budget_amount,
            'budget_hint': budget_hint[:500] if budget_hint else None,
            'contact_email': contact_email,
            'contact_phone': contact_phone,
            'contact_url': contact_url,
        }
