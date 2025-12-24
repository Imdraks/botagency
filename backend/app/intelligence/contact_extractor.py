"""
Contact Extractor - Extraction intelligente des informations de contact
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ContactType(str, Enum):
    BOOKING = "booking"  # Contact booking artiste
    COMMERCIAL = "commercial"  # Contact commercial
    PRESS = "press"  # Contact presse
    GENERAL = "general"  # Contact général
    TENDER = "tender"  # Contact appel d'offres


@dataclass
class ExtractedContact:
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    role: Optional[str]
    company: Optional[str]
    contact_type: ContactType
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'company': self.company,
            'type': self.contact_type.value,
            'confidence': self.confidence,
        }


class ContactExtractor:
    """
    Extracteur intelligent de contacts qui :
    - Détecte emails, téléphones, noms
    - Identifie le type de contact (booking, commercial, presse, etc.)
    - Associe les informations entre elles
    """
    
    def __init__(self):
        # Patterns pour les rôles
        self.role_patterns = {
            ContactType.BOOKING: [
                r'booking', r'management', r'agent', r'tourneur', 
                r'producteur', r'manager'
            ],
            ContactType.COMMERCIAL: [
                r'commercial', r'business', r'vente', r'partenariat',
                r'sponsoring', r'direction commerciale'
            ],
            ContactType.PRESS: [
                r'press', r'presse', r'communication', r'média',
                r'relations publiques', r'rp'
            ],
            ContactType.TENDER: [
                r'marché', r'appel d\'offres', r'achat', r'procurement',
                r'correspondant', r'dce', r'dossier'
            ],
        }
        
        # Patterns pour les noms
        self.name_patterns = [
            r'(?:contact|responsable|chargé[e]?|directeur|directrice)[:\s]+([A-ZÀ-Ÿ][a-zà-ÿ]+\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)',
            r'([A-ZÀ-Ÿ][a-zà-ÿ]+\s+[A-ZÀ-Ÿ]{2,})',  # Prénom NOM
        ]
    
    def extract_contacts(self, text: str) -> List[ExtractedContact]:
        """
        Extrait tous les contacts d'un texte
        """
        contacts = []
        
        # Extraire les emails
        emails = self._extract_emails(text)
        
        # Extraire les téléphones
        phones = self._extract_phones(text)
        
        # Pour chaque email, essayer de trouver les infos associées
        for email in emails:
            contact = self._build_contact_from_email(email, text)
            if contact:
                contacts.append(contact)
        
        # Pour les téléphones sans email associé
        for phone in phones:
            if not any(c.phone == phone for c in contacts):
                contact = self._build_contact_from_phone(phone, text)
                if contact:
                    contacts.append(contact)
        
        # Dédupliquer
        contacts = self._deduplicate(contacts)
        
        return contacts
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extrait les adresses email"""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = list(set(re.findall(pattern, text, re.IGNORECASE)))
        
        # Filtrer les emails génériques/invalides
        invalid_patterns = [
            'example.com', 'test.com', 'email.com', 'domain.com',
            'noreply', 'no-reply', 'donotreply', 'unsubscribe'
        ]
        
        return [e for e in emails if not any(p in e.lower() for p in invalid_patterns)]
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extrait les numéros de téléphone"""
        patterns = [
            r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}',  # Format français
            r'\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
        ]
        
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        
        # Nettoyer et dédupliquer
        cleaned = []
        for phone in phones:
            # Normaliser
            normalized = re.sub(r'[\s.-]', '', phone)
            if len(normalized) >= 10 and normalized not in cleaned:
                cleaned.append(phone)
        
        return cleaned[:10]
    
    def _build_contact_from_email(self, email: str, text: str) -> Optional[ExtractedContact]:
        """Construit un contact à partir d'un email"""
        
        # Trouver le contexte autour de l'email
        email_idx = text.lower().find(email.lower())
        if email_idx == -1:
            return None
        
        start = max(0, email_idx - 200)
        end = min(len(text), email_idx + 200)
        context = text[start:end]
        
        # Déterminer le type de contact
        contact_type = self._determine_contact_type(context, email)
        
        # Chercher un nom associé
        name = self._find_associated_name(context)
        
        # Chercher un rôle
        role = self._find_role(context)
        
        # Chercher un téléphone proche
        phones = self._extract_phones(context)
        phone = phones[0] if phones else None
        
        # Chercher une entreprise
        company = self._find_company(context)
        
        # Calculer la confiance
        confidence = self._calculate_confidence(email, name, phone, role)
        
        return ExtractedContact(
            name=name,
            email=email,
            phone=phone,
            role=role,
            company=company,
            contact_type=contact_type,
            confidence=confidence,
        )
    
    def _build_contact_from_phone(self, phone: str, text: str) -> Optional[ExtractedContact]:
        """Construit un contact à partir d'un téléphone"""
        
        # Trouver le contexte autour du téléphone
        phone_idx = text.find(phone)
        if phone_idx == -1:
            return None
        
        start = max(0, phone_idx - 200)
        end = min(len(text), phone_idx + 200)
        context = text[start:end]
        
        contact_type = self._determine_contact_type(context, None)
        name = self._find_associated_name(context)
        role = self._find_role(context)
        company = self._find_company(context)
        
        return ExtractedContact(
            name=name,
            email=None,
            phone=phone,
            role=role,
            company=company,
            contact_type=contact_type,
            confidence=0.4,  # Moins confiant sans email
        )
    
    def _determine_contact_type(self, context: str, email: Optional[str]) -> ContactType:
        """Détermine le type de contact"""
        context_lower = context.lower()
        email_lower = email.lower() if email else ""
        
        # Vérifier les patterns pour chaque type
        for contact_type, patterns in self.role_patterns.items():
            for pattern in patterns:
                if re.search(pattern, context_lower) or re.search(pattern, email_lower):
                    return contact_type
        
        # Deviner par le préfixe de l'email
        if email:
            email_prefix = email.split('@')[0].lower()
            if any(x in email_prefix for x in ['booking', 'management', 'agent']):
                return ContactType.BOOKING
            if any(x in email_prefix for x in ['contact', 'info', 'hello']):
                return ContactType.GENERAL
            if any(x in email_prefix for x in ['press', 'presse', 'media']):
                return ContactType.PRESS
            if any(x in email_prefix for x in ['commercial', 'business', 'sales']):
                return ContactType.COMMERCIAL
        
        return ContactType.GENERAL
    
    def _find_associated_name(self, context: str) -> Optional[str]:
        """Trouve un nom associé dans le contexte"""
        for pattern in self.name_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1).strip()
        return None
    
    def _find_role(self, context: str) -> Optional[str]:
        """Trouve le rôle/fonction dans le contexte"""
        role_keywords = [
            r'(directeur|directrice)\s+\w+',
            r'(responsable)\s+\w+',
            r'(chargé[e]?)\s+\w+',
            r'(manager)',
            r'(agent)',
            r'(booking)',
        ]
        
        for pattern in role_keywords:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return None
    
    def _find_company(self, context: str) -> Optional[str]:
        """Trouve le nom d'entreprise dans le contexte"""
        # Patterns pour les entreprises
        patterns = [
            r'(?:chez|at|@)\s+([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)*)',
            r'([A-ZÀ-Ÿ][a-zà-ÿ]+\s+(?:Agency|Production|Management|Entertainment|Records|Music))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _calculate_confidence(
        self,
        email: str,
        name: Optional[str],
        phone: Optional[str],
        role: Optional[str]
    ) -> float:
        """Calcule la confiance du contact"""
        confidence = 0.5  # Base
        
        # Email valide
        if email and '@' in email:
            confidence += 0.2
        
        # Nom trouvé
        if name:
            confidence += 0.15
        
        # Téléphone
        if phone:
            confidence += 0.1
        
        # Rôle identifié
        if role:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _deduplicate(self, contacts: List[ExtractedContact]) -> List[ExtractedContact]:
        """Supprime les contacts en double"""
        seen_emails = set()
        seen_phones = set()
        unique = []
        
        for contact in sorted(contacts, key=lambda c: c.confidence, reverse=True):
            is_duplicate = False
            
            if contact.email and contact.email.lower() in seen_emails:
                is_duplicate = True
            if contact.phone and contact.phone in seen_phones:
                is_duplicate = True
            
            if not is_duplicate:
                if contact.email:
                    seen_emails.add(contact.email.lower())
                if contact.phone:
                    seen_phones.add(contact.phone)
                unique.append(contact)
        
        return unique
    
    def get_booking_contact(self, text: str) -> Optional[ExtractedContact]:
        """Retourne le contact booking si trouvé"""
        contacts = self.extract_contacts(text)
        booking = [c for c in contacts if c.contact_type == ContactType.BOOKING]
        return booking[0] if booking else None
