"""
Wikidata Provider for management information
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import httpx

from .base import BaseProvider

logger = logging.getLogger(__name__)


class WikidataProvider(BaseProvider):
    """
    Fetches management information from Wikidata
    Matching: P1902 (Spotify artist ID)
    Management: P1037 (director/manager)
    """
    
    WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
    
    async def fetch(self, artist_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch management info from Wikidata"""
        
        # SPARQL query to find entity by Spotify ID and get management
        query = f"""
        SELECT ?entity ?entityLabel ?manager ?managerLabel WHERE {{
          ?entity wdt:P1902 "{artist_id}".
          OPTIONAL {{ ?entity wdt:P1037 ?manager }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr". }}
        }}
        LIMIT 1
        """
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_wikidata) as client:
                response = await client.get(
                    self.WIKIDATA_SPARQL_ENDPOINT,
                    params={
                        "query": query,
                        "format": "json"
                    },
                    headers={
                        "User-Agent": "OpportunitiesRadar/1.0 (https://youragency.com)"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Wikidata returned {response.status_code}")
                    raise Exception(f"Wikidata API error: {response.status_code}")
                
                data = response.json()
                bindings = data.get("results", {}).get("bindings", [])
                
                if not bindings:
                    logger.info(f"No Wikidata entity found for Spotify ID {artist_id}")
                    return {
                        "value": None,
                        "provider": "wikidata",
                        "retrieved_at": datetime.now(),
                        "confidence": 0.0,
                        "evidence": {
                            "wikidata_entity": None,
                            "match_property": "P1902",
                            "management_property": "P1037"
                        }
                    }
                
                result = bindings[0]
                entity_id = result["entity"]["value"].split("/")[-1]
                manager_label = result.get("managerLabel", {}).get("value")
                
                confidence = 1.0 if manager_label else 0.0
                
                return {
                    "value": manager_label or "unknown",
                    "provider": "wikidata",
                    "retrieved_at": datetime.now(),
                    "confidence": confidence,
                    "evidence": {
                        "wikidata_entity": entity_id,
                        "match_property": "P1902",
                        "management_property": "P1037"
                    }
                }
                
        except Exception as e:
            logger.error(f"Wikidata error for {artist_id}: {e}")
            raise
