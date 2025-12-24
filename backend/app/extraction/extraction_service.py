"""
LLM-based extraction service for documents and briefs.
Extracts contacts, events, entities from documents and generates briefs.
"""
import json
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx

from app.core.config import settings
from app.db.models.entity import ObjectiveType

logger = logging.getLogger(__name__)


# ========================
# PROMPTS
# ========================

EXTRACT_DOCUMENT_PROMPT = """Tu es un assistant d'extraction d'informations. Analyse ce document et extrais les informations structurées.

DOCUMENT:
Titre: {title}
Source: {source_name}
URL: {url}
Date: {published_at}
Contenu:
{content}

OBJECTIF DE RECHERCHE: {objective}
ENTITÉ RECHERCHÉE: {entity_name}

Extrais les informations suivantes au format JSON:

{{
  "summary": "Résumé en 2-3 phrases du contenu pertinent pour l'entité recherchée",
  "contacts_found": [
    {{
      "type": "EMAIL|FORM|BOOKING|PRESS|AGENT|MANAGEMENT|SOCIAL|PHONE",
      "value": "valeur du contact",
      "context": "où/comment ce contact a été trouvé",
      "is_official": true/false
    }}
  ],
  "entities_found": [
    {{
      "name": "nom de l'entité mentionnée",
      "type": "PERSON|ORGANIZATION|TOPIC",
      "context": "contexte de la mention"
    }}
  ],
  "event_signals": [
    {{
      "type": "CONCERT|RELEASE|COLLABORATION|ANNOUNCEMENT|AWARD|INTERVIEW",
      "date": "YYYY-MM-DD si connue, sinon null",
      "description": "description de l'événement",
      "relevance_score": 0.0-1.0
    }}
  ],
  "opportunity_type": "SPONSOR|BOOKING|PRESS|VENUE|SUPPLIER|GRANT|null",
  "confidence": 0.0-1.0
}}

RÈGLES:
- Ne retourne QUE le JSON, sans texte avant ou après
- Pour les emails, vérifie qu'ils sont valides (contiennent @)
- Pour les téléphones, normalise au format international si possible
- is_official = true si le contact vient du site officiel de l'entité
- confidence = degré de pertinence du document pour l'objectif
- Si aucune info trouvée, retourne des tableaux vides

JSON:"""


GENERATE_BRIEF_PROMPT = """Tu es un assistant de veille stratégique. Génère un brief exploitable à partir des extractions ci-dessous.

ENTITÉ: {entity_name} ({entity_type})
OBJECTIF: {objective}
PÉRIODE: {timeframe_days} derniers jours

EXTRACTIONS COLLECTÉES:
{extractions_json}

CONTACTS EXISTANTS:
{existing_contacts_json}

Génère un brief structuré au format JSON:

{{
  "overview": "Paragraphe de synthèse (3-5 phrases) sur l'entité dans le contexte de l'objectif. Mentionne les points clés, l'actualité récente, et la pertinence pour l'objectif.",
  
  "contacts_ranked": [
    {{
      "type": "EMAIL|BOOKING|PRESS|AGENT|etc",
      "value": "contact",
      "label": "description (ex: Booking France, Press Contact)",
      "reliability_score": -10 à +10,
      "source": "d'où vient ce contact"
    }}
  ],
  
  "useful_facts": [
    {{
      "fact": "Information utile et actionnable",
      "source": "source de l'info",
      "category": "CAREER|BUSINESS|SOCIAL|EVENT|MEDIA"
    }}
  ],
  
  "timeline": [
    {{
      "date": "YYYY-MM-DD ou 'Récent' ou 'À venir'",
      "event_type": "CONCERT|RELEASE|COLLABORATION|ANNOUNCEMENT|etc",
      "description": "description courte",
      "source": "source"
    }}
  ],
  
  "completeness_score": 0.0-1.0
}}

SCORING DES CONTACTS:
+3 = domaine officiel de l'entité (site web, bio réseau social vérifié)
+2 = page contact/presse/booking dédiée
+1 = mention dans média sérieux
-1 = source non vérifiée
-3 = source douteuse (forum, commentaire)

RÈGLES:
- Trie contacts_ranked par reliability_score décroissant
- Limite à 5 contacts max (les plus fiables)
- Limite à 10 useful_facts max
- Timeline: événements des {timeframe_days} derniers jours + à venir
- completeness_score: 1.0 si contacts fiables + infos récentes, 0.0 si rien trouvé
- Ne retourne QUE le JSON valide

JSON:"""


# ========================
# EXTRACTION SERVICE
# ========================

class ExtractionService:
    """Service for LLM-based extraction and brief generation"""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = getattr(settings, 'extraction_model', 'gpt-4o-mini')
        self.base_url = "https://api.openai.com/v1"
    
    async def extract_document(
        self,
        title: str,
        content: str,
        source_name: str,
        url: str = None,
        published_at: datetime = None,
        entity_name: str = None,
        objective: str = "BOOKING"
    ) -> Dict[str, Any]:
        """
        Extract structured information from a document.
        Returns: {summary, contacts_found, entities_found, event_signals, opportunity_type, confidence}
        """
        if not self.api_key:
            logger.warning("No OpenAI API key configured, using regex extraction")
            return self._regex_extract(content, title, url)
        
        prompt = EXTRACT_DOCUMENT_PROMPT.format(
            title=title or "Sans titre",
            source_name=source_name or "Unknown",
            url=url or "N/A",
            published_at=published_at.isoformat() if published_at else "N/A",
            content=content[:4000] if content else "",  # Limit content
            objective=objective,
            entity_name=entity_name or "N/A"
        )
        
        try:
            result = await self._call_llm(prompt)
            return self._parse_json_response(result, default={
                "summary": None,
                "contacts_found": [],
                "entities_found": [],
                "event_signals": [],
                "opportunity_type": None,
                "confidence": 0.0
            })
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._regex_extract(content, title, url)
    
    async def generate_brief(
        self,
        entity_name: str,
        entity_type: str,
        objective: str,
        timeframe_days: int,
        extractions: List[Dict[str, Any]],
        existing_contacts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a synthesized brief from multiple extractions.
        Returns: {overview, contacts_ranked, useful_facts, timeline, completeness_score}
        """
        if not self.api_key:
            logger.warning("No OpenAI API key, generating basic brief")
            return self._basic_brief(extractions, existing_contacts)
        
        prompt = GENERATE_BRIEF_PROMPT.format(
            entity_name=entity_name,
            entity_type=entity_type,
            objective=objective,
            timeframe_days=timeframe_days,
            extractions_json=json.dumps(extractions[:20], ensure_ascii=False, indent=2),
            existing_contacts_json=json.dumps(existing_contacts[:10], ensure_ascii=False, indent=2)
        )
        
        try:
            result = await self._call_llm(prompt, max_tokens=2000)
            return self._parse_json_response(result, default={
                "overview": None,
                "contacts_ranked": [],
                "useful_facts": [],
                "timeline": [],
                "completeness_score": 0.0
            })
        except Exception as e:
            logger.error(f"Brief generation failed: {e}")
            return self._basic_brief(extractions, existing_contacts)
    
    async def _call_llm(self, prompt: str, max_tokens: int = 1500) -> str:
        """Call OpenAI API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "Tu es un assistant d'extraction de données. Réponds uniquement en JSON valide."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def _parse_json_response(self, response: str, default: Dict) -> Dict:
        """Parse JSON from LLM response, handling markdown code blocks"""
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```"):
            response = re.sub(r'^```(?:json)?\n?', '', response)
            response = re.sub(r'\n?```$', '', response)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return default
    
    def _regex_extract(self, content: str, title: str, url: str) -> Dict[str, Any]:
        """Fallback regex-based extraction"""
        contacts = []
        
        # Extract emails
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', content or "")
        for email in set(emails):
            contacts.append({
                "type": "EMAIL",
                "value": email.lower(),
                "context": "Extrait du contenu",
                "is_official": False
            })
        
        # Extract phone numbers (French format)
        phones = re.findall(r'(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}', content or "")
        for phone in set(phones):
            contacts.append({
                "type": "PHONE",
                "value": re.sub(r'[\s.-]', '', phone),
                "context": "Extrait du contenu",
                "is_official": False
            })
        
        return {
            "summary": title[:200] if title else None,
            "contacts_found": contacts[:5],
            "entities_found": [],
            "event_signals": [],
            "opportunity_type": None,
            "confidence": 0.3 if contacts else 0.1
        }
    
    def _basic_brief(
        self,
        extractions: List[Dict],
        existing_contacts: List[Dict]
    ) -> Dict[str, Any]:
        """Generate basic brief without LLM"""
        # Aggregate contacts
        contacts = []
        for ext in extractions:
            for c in ext.get("contacts_found", []):
                contacts.append({
                    "type": c.get("type", "EMAIL"),
                    "value": c.get("value"),
                    "label": c.get("context"),
                    "reliability_score": 1 if c.get("is_official") else 0,
                    "source": "extraction"
                })
        
        # Add existing contacts
        for c in existing_contacts:
            contacts.append({
                "type": c.get("contact_type", c.get("type")),
                "value": c.get("value"),
                "label": c.get("label"),
                "reliability_score": c.get("reliability_score", 0),
                "source": c.get("source_name")
            })
        
        # Dedupe and sort
        seen = set()
        unique_contacts = []
        for c in contacts:
            key = f"{c['type']}:{c['value']}"
            if key not in seen:
                seen.add(key)
                unique_contacts.append(c)
        unique_contacts.sort(key=lambda x: x.get("reliability_score", 0), reverse=True)
        
        # Aggregate events
        timeline = []
        for ext in extractions:
            for ev in ext.get("event_signals", []):
                timeline.append({
                    "date": ev.get("date"),
                    "event_type": ev.get("type"),
                    "description": ev.get("description"),
                    "source": "extraction"
                })
        
        # Build overview from summaries
        summaries = [ext.get("summary") for ext in extractions if ext.get("summary")]
        overview = " ".join(summaries[:3]) if summaries else None
        
        completeness = min(1.0, (len(unique_contacts) * 0.2 + len(timeline) * 0.1 + (0.3 if overview else 0)))
        
        return {
            "overview": overview,
            "contacts_ranked": unique_contacts[:5],
            "useful_facts": [],
            "timeline": timeline[:10],
            "completeness_score": completeness
        }


# ========================
# CONTACT RELIABILITY SCORER
# ========================

class ContactReliabilityScorer:
    """Scores contact reliability based on source and context"""
    
    # Trusted domains
    TRUSTED_DOMAINS = {
        "official": 3,   # Site officiel de l'artiste/org
        "social_verified": 2,  # Réseaux sociaux vérifiés
    }
    
    # Page types that indicate reliability
    PAGE_TYPES = {
        "contact": 2,
        "presse": 2,
        "press": 2,
        "booking": 2,
        "management": 2,
        "about": 1,
        "bio": 1,
    }
    
    # Trusted media sources
    TRUSTED_MEDIA = [
        "lesinrocks", "telerama", "liberation", "lemonde", "lefigaro",
        "rollingstone", "billboard", "pitchfork", "nme", "guardian",
        "tsugi", "traxmag", "residentadvisor", "ra.co", "cnm.fr"
    ]
    
    # Untrusted sources
    UNTRUSTED_SOURCES = [
        "forum", "reddit", "comment", "facebook.com/groups",
        "quora", "yahoo", "ask.com"
    ]
    
    @classmethod
    def score_contact(
        cls,
        contact_type: str,
        value: str,
        source_url: str = None,
        source_name: str = None,
        is_official_source: bool = False,
        page_context: str = None
    ) -> int:
        """
        Calculate reliability score for a contact.
        Range: -10 to +10
        """
        score = 0
        
        # Official source bonus
        if is_official_source:
            score += 3
        
        # Check page type in URL
        if source_url:
            url_lower = source_url.lower()
            for page_type, points in cls.PAGE_TYPES.items():
                if page_type in url_lower:
                    score += points
                    break
            
            # Trusted media
            for media in cls.TRUSTED_MEDIA:
                if media in url_lower:
                    score += 1
                    break
            
            # Untrusted sources
            for untrusted in cls.UNTRUSTED_SOURCES:
                if untrusted in url_lower:
                    score -= 3
                    break
        
        # Email domain analysis
        if contact_type == "EMAIL" and "@" in value:
            domain = value.split("@")[1].lower()
            # Generic email domains are less reliable
            if domain in ["gmail.com", "yahoo.fr", "hotmail.com", "outlook.com"]:
                score -= 1
            # Professional domains are more reliable
            elif any(x in domain for x in ["booking", "press", "management", "agency"]):
                score += 1
        
        # Booking/Press contact types are inherently more useful
        if contact_type in ["BOOKING", "PRESS", "MANAGEMENT", "AGENT"]:
            score += 1
        
        return max(-10, min(10, score))


# Singleton instance
extraction_service = ExtractionService()
contact_scorer = ContactReliabilityScorer()
