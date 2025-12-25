"""
AI-powered collection tasks using ChatGPT.
This handles the "Advanced Collection" that uses OpenAI to search and generate briefs.
"""
import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from openai import OpenAI

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models.entity import (
    Entity, EntityType, Document, Brief, CollectionRun, 
    ObjectiveType, Contact, ContactType
)
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_db():
    """Get database session"""
    return SessionLocal()


def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client if API key is configured"""
    if not settings.openai_api_key:
        logger.warning("OpenAI API key not configured")
        return None
    return OpenAI(api_key=settings.openai_api_key)


OBJECTIVE_PROMPTS = {
    "SPONSOR": """Tu es un expert en recherche de sponsors et partenaires.
Recherche des informations sur les sponsors potentiels, marques partenaires, et opportunités de partenariat pour {entity_name}.
Focus: budgets marketing, départements partenariats, contacts décisionnaires, historique de sponsoring.""",

    "BOOKING": """Tu es un expert en booking artistique.
Recherche des informations sur les opportunités de booking pour {entity_name}.
Focus: programmateurs, directeurs artistiques, dates disponibles, cachets, conditions techniques, contacts booking.""",

    "PRESS": """Tu es un expert en relations presse et médias.
Recherche des contacts presse, journalistes, et médias pertinents pour {entity_name}.
Focus: attachés de presse, journalistes culture/musique, médias spécialisés, émissions TV/radio.""",

    "VENUE": """Tu es un expert en recherche de lieux événementiels.
Recherche des salles, lieux de concerts, et espaces événementiels pour {entity_name}.
Focus: capacité, équipements techniques, tarifs de location, disponibilités, contacts booking.""",

    "SUPPLIER": """Tu es un expert en prestataires événementiels.
Recherche des prestataires techniques et logistiques pour {entity_name}.
Focus: son/lumière, scénographie, traiteur, sécurité, logistique, tarifs.""",

    "GRANT": """Tu es un expert en subventions et aides culturelles.
Recherche des subventions, appels à projets et aides disponibles pour {entity_name}.
Focus: montants, critères d'éligibilité, dates limites, contacts, documents requis."""
}


def build_search_prompt(
    entity_name: str,
    entity_type: str,
    objective: str,
    secondary_keywords: List[str],
    region: Optional[str] = None,
    city: Optional[str] = None,
) -> str:
    """Build the search prompt for ChatGPT"""
    base_prompt = OBJECTIVE_PROMPTS.get(objective, OBJECTIVE_PROMPTS["SPONSOR"])
    base_prompt = base_prompt.format(entity_name=entity_name)
    
    location_context = ""
    if city:
        location_context = f"Zone géographique prioritaire: {city}"
    elif region:
        location_context = f"Zone géographique prioritaire: {region}"
    
    keywords_context = ""
    if secondary_keywords:
        keywords_context = f"Mots-clés additionnels à considérer: {', '.join(secondary_keywords)}"
    
    full_prompt = f"""{base_prompt}

Entité recherchée: {entity_name} (type: {entity_type})
{location_context}
{keywords_context}

IMPORTANT: Retourne tes résultats au format JSON avec la structure suivante:
{{
  "summary": "Résumé exécutif de ta recherche (2-3 phrases)",
  "opportunities": [
    {{
      "title": "Titre de l'opportunité",
      "description": "Description détaillée",
      "organization": "Nom de l'organisation/entreprise",
      "relevance_score": 85,
      "contact_name": "Nom du contact (si trouvé)",
      "contact_role": "Rôle/fonction",
      "contact_email": "email@example.com (si trouvé)",
      "contact_phone": "+33... (si trouvé)",
      "budget_estimate": "Estimation budget si applicable",
      "deadline": "Date limite si applicable",
      "location": "Localisation",
      "source_info": "D'où vient cette information",
      "action_items": ["Action recommandée 1", "Action 2"]
    }}
  ],
  "contacts": [
    {{
      "name": "Nom complet",
      "role": "Fonction/titre",
      "organization": "Organisation",
      "email": "email si trouvé",
      "phone": "téléphone si trouvé",
      "linkedin": "URL LinkedIn si trouvé",
      "relevance": "Pourquoi ce contact est pertinent"
    }}
  ],
  "useful_facts": [
    "Fait important 1",
    "Fait important 2"
  ],
  "recommended_next_steps": [
    "Étape recommandée 1",
    "Étape recommandée 2"
  ]
}}

Fournis des informations concrètes, actionnables et vérifiables. 
Indique clairement quand une information est une estimation ou supposition.
Score de pertinence de 0 à 100 basé sur la correspondance avec l'objectif.
"""
    return full_prompt


def parse_ai_response(response_text: str) -> Dict[str, Any]:
    """Parse the AI response JSON"""
    try:
        # Try to extract JSON from the response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            return json.loads(json_match.group())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response JSON: {e}")
    
    # Return a basic structure if parsing fails
    return {
        "summary": response_text[:500] if response_text else "Aucun résultat",
        "opportunities": [],
        "contacts": [],
        "useful_facts": [],
        "recommended_next_steps": []
    }


def calculate_opportunity_score(opp: Dict[str, Any], objective: str) -> int:
    """Calculate a score for an AI-found opportunity"""
    score = opp.get('relevance_score', 50)
    
    # Bonus for having contact info
    if opp.get('contact_email'):
        score += 10
    if opp.get('contact_phone'):
        score += 5
    if opp.get('contact_name'):
        score += 5
    
    # Bonus for budget info
    if opp.get('budget_estimate'):
        score += 10
    
    # Bonus for deadline (urgency)
    if opp.get('deadline'):
        score += 5
    
    # Cap at 100
    return min(score, 100)


@celery_app.task(bind=True, max_retries=2)
def run_ai_collection_task(
    self,
    run_id: str,
    entity_ids: List[str],
    objective: str,
    secondary_keywords: List[str] = None,
    timeframe_days: int = 30,
    require_contact: bool = False,
    filters: Dict[str, Any] = None,
):
    """
    AI-powered collection task using ChatGPT.
    
    1. Build intelligent prompts based on entity and objective
    2. Query ChatGPT for relevant opportunities
    3. Parse and score results
    4. Generate comprehensive brief
    """
    db = get_db()
    filters = filters or {}
    client = get_openai_client()
    
    try:
        # Get collection run
        collection_run = db.query(CollectionRun).filter(
            CollectionRun.id == run_id
        ).first()
        
        if not collection_run:
            logger.error(f"Collection run not found: {run_id}")
            return {"error": "Collection run not found"}
        
        # Check OpenAI availability
        if not client:
            collection_run.status = "FAILED"
            collection_run.error_summary = "OpenAI API key not configured. Please set OPENAI_API_KEY."
            collection_run.finished_at = datetime.utcnow()
            db.commit()
            return {"error": "OpenAI API key not configured"}
        
        # Get entities
        entities = db.query(Entity).filter(
            Entity.id.in_([UUID(eid) for eid in entity_ids])
        ).all()
        
        if not entities:
            collection_run.status = "FAILED"
            collection_run.error_summary = "Entities not found"
            collection_run.finished_at = datetime.utcnow()
            db.commit()
            return {"error": "Entities not found"}
        
        logger.info(f"Starting AI collection for {len(entities)} entities with objective: {objective}")
        
        all_opportunities = []
        all_contacts = []
        all_facts = []
        all_steps = []
        summaries = []
        
        # Process each entity with ChatGPT
        for entity in entities:
            try:
                # Build prompt
                prompt = build_search_prompt(
                    entity_name=entity.name,
                    entity_type=entity.entity_type.value,
                    objective=objective,
                    secondary_keywords=secondary_keywords or [],
                    region=filters.get('region'),
                    city=filters.get('city'),
                )
                
                # Call ChatGPT
                logger.info(f"Querying ChatGPT for entity: {entity.name}")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # Use gpt-4o-mini for cost efficiency
                    messages=[
                        {
                            "role": "system",
                            "content": "Tu es un assistant expert en recherche business et veille stratégique. Tu fournis des informations précises, actionnables et bien structurées."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                
                response_text = response.choices[0].message.content
                parsed = parse_ai_response(response_text)
                
                # Collect results
                if parsed.get('summary'):
                    summaries.append(f"**{entity.name}**: {parsed['summary']}")
                
                for opp in parsed.get('opportunities', []):
                    opp['entity_name'] = entity.name
                    opp['entity_id'] = str(entity.id)
                    opp['score'] = calculate_opportunity_score(opp, objective)
                    all_opportunities.append(opp)
                
                for contact in parsed.get('contacts', []):
                    contact['entity_name'] = entity.name
                    contact['entity_id'] = str(entity.id)
                    all_contacts.append(contact)
                
                all_facts.extend(parsed.get('useful_facts', []))
                all_steps.extend(parsed.get('recommended_next_steps', []))
                
                # Store contacts in database
                for contact_data in parsed.get('contacts', []):
                    try:
                        contact = Contact(
                            entity_id=entity.id,
                            name=contact_data.get('name', 'Unknown'),
                            role=contact_data.get('role'),
                            organization=contact_data.get('organization'),
                            email=contact_data.get('email'),
                            phone=contact_data.get('phone'),
                            linkedin_url=contact_data.get('linkedin'),
                            contact_type=ContactType.AI_FOUND,
                            relevance_score=80,
                            notes=contact_data.get('relevance', ''),
                        )
                        db.add(contact)
                    except Exception as e:
                        logger.warning(f"Failed to save contact: {e}")
                
            except Exception as e:
                logger.error(f"Error processing entity {entity.name}: {e}")
                continue
        
        # Filter by require_contact if needed
        if require_contact:
            all_opportunities = [
                opp for opp in all_opportunities 
                if opp.get('contact_email') or opp.get('contact_phone')
            ]
        
        # Sort by score
        all_opportunities.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Create brief for the first entity (or combined)
        main_entity = entities[0]
        
        brief = Brief(
            entity_id=main_entity.id,
            objective=ObjectiveType[objective],
            overview="\n\n".join(summaries) if summaries else "Collecte terminée",
            useful_facts=all_facts[:10],  # Top 10 facts
            timeline_events=[],
            contacts_ranked=[
                {
                    "name": c.get('name'),
                    "role": c.get('role'),
                    "organization": c.get('organization'),
                    "email": c.get('email'),
                    "phone": c.get('phone'),
                    "relevance": c.get('relevance', '')
                }
                for c in all_contacts[:10]
            ],
            sources_used=[{"name": "ChatGPT AI", "type": "AI", "relevance": "high"}],
            recommendations=all_steps[:5],
            confidence_score=min(85, 50 + len(all_opportunities) * 5),
            generated_at=datetime.utcnow(),
            raw_ai_output={
                "opportunities": all_opportunities,
                "all_contacts": all_contacts,
                "all_facts": all_facts,
                "all_steps": all_steps,
            }
        )
        db.add(brief)
        db.flush()
        
        # Update collection run
        collection_run.status = "SUCCESS"
        collection_run.finished_at = datetime.utcnow()
        collection_run.documents_new = len(all_opportunities)
        collection_run.contacts_found = len(all_contacts)
        collection_run.brief_id = brief.id
        collection_run.sources_success = 1
        collection_run.source_runs = [{
            "source_id": "openai",
            "source_name": "ChatGPT AI",
            "status": "SUCCESS",
            "items_found": len(all_opportunities),
            "items_new": len(all_opportunities),
            "latency_ms": 0,
            "error": None
        }]
        
        db.commit()
        
        logger.info(f"AI collection completed: {len(all_opportunities)} opportunities, {len(all_contacts)} contacts")
        
        return {
            "run_id": run_id,
            "status": "SUCCESS",
            "brief_id": str(brief.id),
            "opportunities_found": len(all_opportunities),
            "contacts_found": len(all_contacts),
        }
        
    except Exception as e:
        logger.error(f"AI collection task failed: {e}")
        if collection_run:
            collection_run.status = "FAILED"
            collection_run.error_summary = str(e)[:1000]
            collection_run.finished_at = datetime.utcnow()
            db.commit()
        raise
    finally:
        db.close()
