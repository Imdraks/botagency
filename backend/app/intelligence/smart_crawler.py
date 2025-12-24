"""
Smart Crawler - Intelligent web navigation and content extraction
Agit comme un navigateur intelligent qui explore le web pour trouver des opportunités
"""
import asyncio
import hashlib
import re
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)


class SmartCrawler:
    """
    Navigateur intelligent qui :
    - Explore les pages liées pertinentes
    - Extrait le contenu riche (texte, liens, métadonnées)
    - Suit les liens vers les détails des opportunités
    - Détecte les patterns de prix, contacts, conditions
    """
    
    def __init__(self, max_depth: int = 2, max_pages: int = 50):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.timeout = settings.ingestion_timeout_seconds
        self.user_agent = settings.ingestion_user_agent
        
        # Patterns pour détecter les pages intéressantes
        self.interesting_patterns = [
            r'artiste|artist',
            r'booking|reservation',
            r'tarif|price|prix|cachet',
            r'contact',
            r'evenement|event|concert|festival',
            r'appel.*offre|tender|marche.*public',
            r'partenariat|partnership|sponsor',
            r'collaboration|collab',
        ]
        
        # Patterns à éviter
        self.avoid_patterns = [
            r'login|connexion|signin',
            r'privacy|confidentialite',
            r'legal|mentions-legales',
            r'cookie',
            r'\.pdf$|\.doc$|\.xls$',
            r'facebook\.com|twitter\.com|instagram\.com|linkedin\.com',
        ]
    
    async def crawl(self, start_url: str, search_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Démarre le crawl intelligent depuis une URL de départ
        
        Args:
            start_url: URL de départ
            search_params: Paramètres de recherche (keywords, region, etc.)
        
        Returns:
            Liste d'opportunités trouvées
        """
        self.visited_urls = set()
        self.search_params = search_params or {}
        opportunities = []
        
        await self._crawl_recursive(start_url, depth=0, opportunities=opportunities)
        
        return opportunities
    
    async def _crawl_recursive(
        self, 
        url: str, 
        depth: int, 
        opportunities: List[Dict[str, Any]]
    ):
        """Crawl récursif avec limite de profondeur"""
        
        if depth > self.max_depth:
            return
        
        if len(self.visited_urls) >= self.max_pages:
            return
        
        # Normaliser l'URL
        url = self._normalize_url(url)
        
        if url in self.visited_urls:
            return
        
        if self._should_skip_url(url):
            return
        
        self.visited_urls.add(url)
        logger.info(f"Crawling [{depth}]: {url}")
        
        try:
            html = await self._fetch_page(url)
            if not html:
                return
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Extraire les informations de la page
            page_data = self._extract_page_data(soup, url)
            
            # Vérifier si c'est une opportunité pertinente
            if self._is_opportunity(page_data):
                opportunities.append(page_data)
                logger.info(f"  ✓ Opportunité trouvée: {page_data.get('title', 'Sans titre')}")
            
            # Trouver les liens intéressants à suivre
            if depth < self.max_depth:
                links = self._find_interesting_links(soup, url)
                
                # Crawler les liens en parallèle (max 5 simultanés)
                tasks = []
                for link in links[:10]:  # Limiter à 10 liens par page
                    tasks.append(
                        self._crawl_recursive(link, depth + 1, opportunities)
                    )
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    async def _fetch_page(self, url: str) -> Optional[str]:
        """Récupère le contenu HTML d'une page"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.text
    
    def _normalize_url(self, url: str) -> str:
        """Normalise une URL"""
        parsed = urlparse(url)
        # Retirer le fragment et normaliser
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
    
    def _should_skip_url(self, url: str) -> bool:
        """Vérifie si l'URL doit être ignorée"""
        url_lower = url.lower()
        for pattern in self.avoid_patterns:
            if re.search(pattern, url_lower):
                return True
        return False
    
    def _is_interesting_url(self, url: str) -> bool:
        """Vérifie si l'URL est potentiellement intéressante"""
        url_lower = url.lower()
        for pattern in self.interesting_patterns:
            if re.search(pattern, url_lower):
                return True
        return False
    
    def _extract_page_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extrait les données structurées d'une page"""
        
        # Titre
        title = None
        if soup.title:
            title = soup.title.string
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
        
        # Description / contenu principal
        description = ""
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            description = meta_desc['content']
        
        # Contenu principal
        main_content = ""
        for selector in ['main', 'article', '.content', '#content', '.post', '.entry']:
            element = soup.select_one(selector)
            if element:
                main_content = element.get_text(separator=' ', strip=True)
                break
        
        if not main_content:
            # Fallback: tout le body
            body = soup.find('body')
            if body:
                main_content = body.get_text(separator=' ', strip=True)[:5000]
        
        # Extraire les emails
        emails = self._extract_emails(str(soup))
        
        # Extraire les téléphones
        phones = self._extract_phones(str(soup))
        
        # Extraire les prix
        prices = self._extract_prices(main_content)
        
        # Extraire les dates
        dates = self._extract_dates(main_content)
        
        # Images
        images = []
        for img in soup.find_all('img', src=True)[:5]:
            img_url = urljoin(url, img['src'])
            images.append(img_url)
        
        return {
            'url': url,
            'title': title,
            'description': description,
            'content': main_content[:3000],
            'emails': emails,
            'phones': phones,
            'prices': prices,
            'dates': dates,
            'images': images,
            'crawled_at': datetime.utcnow().isoformat(),
            'external_id': hashlib.sha256(url.encode()).hexdigest()[:32],
        }
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extrait les adresses email"""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = list(set(re.findall(pattern, text)))
        # Filtrer les emails génériques
        generic = ['example.com', 'test.com', 'email.com']
        return [e for e in emails if not any(g in e for g in generic)][:5]
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extrait les numéros de téléphone (format français)"""
        patterns = [
            r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}',  # Format français
            r'\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
        ]
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))[:3]
    
    def _extract_prices(self, text: str) -> List[Dict[str, Any]]:
        """Extrait les prix mentionnés"""
        prices = []
        
        # Patterns de prix
        patterns = [
            # "10 000 €" ou "10000€"
            (r'(\d{1,3}(?:[\s\u00a0]?\d{3})*)\s*(?:€|euros?|EUR)', 'EUR'),
            # "à partir de 5000€"
            (r'(?:à partir de|from|depuis)\s*(\d{1,3}(?:[\s\u00a0]?\d{3})*)\s*(?:€|euros?)', 'EUR_MIN'),
            # "entre 5000 et 10000€"
            (r'entre\s*(\d{1,3}(?:[\s\u00a0]?\d{3})*)\s*et\s*(\d{1,3}(?:[\s\u00a0]?\d{3})*)\s*(?:€|euros?)', 'EUR_RANGE'),
            # "budget: 50k" ou "50K€"
            (r'(\d+)\s*[kK]\s*(?:€|euros?)?', 'EUR_K'),
            # Cachet artiste
            (r'cachet[:\s]+(\d{1,3}(?:[\s\u00a0]?\d{3})*)\s*(?:€|euros?)?', 'CACHET'),
        ]
        
        for pattern, price_type in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        # Range
                        if len(match) == 2:
                            min_val = int(re.sub(r'[\s\u00a0]', '', match[0]))
                            max_val = int(re.sub(r'[\s\u00a0]', '', match[1]))
                            prices.append({
                                'type': price_type,
                                'min': min_val,
                                'max': max_val,
                                'currency': 'EUR'
                            })
                    else:
                        value = int(re.sub(r'[\s\u00a0]', '', match))
                        if price_type == 'EUR_K':
                            value *= 1000
                        prices.append({
                            'type': price_type,
                            'value': value,
                            'currency': 'EUR'
                        })
                except ValueError:
                    continue
        
        return prices[:10]
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extrait les dates mentionnées"""
        patterns = [
            r'\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}',
            r'\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}',
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(dates))[:5]
    
    def _find_interesting_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Trouve les liens intéressants à suivre"""
        links = []
        base_domain = urlparse(base_url).netloc
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # Ignorer les ancres et javascript
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Construire l'URL complète
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            
            # Rester sur le même domaine
            if parsed.netloc != base_domain:
                continue
            
            # Vérifier si l'URL est intéressante
            if self._is_interesting_url(full_url):
                links.append(full_url)
            
            # Ou si le texte du lien est intéressant
            link_text = a.get_text(strip=True).lower()
            for pattern in self.interesting_patterns:
                if re.search(pattern, link_text):
                    links.append(full_url)
                    break
        
        return list(set(links))
    
    def _is_opportunity(self, page_data: Dict[str, Any]) -> bool:
        """Détermine si une page représente une opportunité"""
        
        # Doit avoir un titre
        if not page_data.get('title'):
            return False
        
        content = f"{page_data.get('title', '')} {page_data.get('description', '')} {page_data.get('content', '')}"
        content_lower = content.lower()
        
        # Indicateurs positifs
        positive_indicators = [
            'appel', 'offre', 'marché', 'consultation',
            'concert', 'festival', 'événement', 'event',
            'booking', 'réservation', 'privatisation',
            'artiste', 'cachet', 'tarif', 'prix',
            'partenariat', 'collaboration', 'sponsor',
            'contact', 'devis', 'demande',
        ]
        
        score = 0
        for indicator in positive_indicators:
            if indicator in content_lower:
                score += 1
        
        # Bonus si on a des infos de contact
        if page_data.get('emails') or page_data.get('phones'):
            score += 2
        
        # Bonus si on a des prix
        if page_data.get('prices'):
            score += 3
        
        # Appliquer les filtres de recherche
        if self.search_params:
            keywords = self.search_params.get('keywords', '')
            if keywords:
                keyword_list = [k.strip().lower() for k in keywords.split(',')]
                for kw in keyword_list:
                    if kw in content_lower:
                        score += 2
        
        return score >= 3
