"""
Database seed script - Create initial data
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.db.models.user import User, Role
from app.db.models.source import SourceConfig
from app.db.models.opportunity import SourceType
from app.db.models.scoring import ScoringRule, RuleType
from app.core.security import get_password_hash
from app.core.config import settings


def seed_users(db):
    """Create default admin user"""
    # Check if admin exists
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@agency.fr")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    admin_name = os.environ.get("ADMIN_NAME", "Administrateur")
    
    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        print(f"Admin user already exists: {admin_email}")
        return
    
    admin = User(
        email=admin_email,
        hashed_password=get_password_hash(admin_password),
        full_name=admin_name,
        role=Role.ADMIN,
        is_active=True,
        is_superuser=True,
    )
    db.add(admin)
    db.commit()
    
    print(f"Admin user created: {admin_email} / {admin_password}")


def seed_sources(db):
    """Create comprehensive sources for opportunities"""
    sources = [
        # =============================================
        # MARCHÉS PUBLICS & APPELS D'OFFRES
        # =============================================
        {
            "name": "BOAMP - Marchés Publics",
            "source_type": SourceType.RSS,
            "description": "Bulletin Officiel des Annonces des Marchés Publics - Source officielle française",
            "url": "https://www.boamp.fr/avis/rss",
            "poll_interval_minutes": 360,
            "is_active": True,
        },
        {
            "name": "Marchés Online",
            "source_type": SourceType.RSS,
            "description": "Portail des marchés publics et privés",
            "url": "https://www.marchesonline.com/appels-offres/rss",
            "poll_interval_minutes": 360,
            "is_active": True,
        },
        {
            "name": "France Marchés",
            "source_type": SourceType.RSS,
            "description": "Veille marchés publics France",
            "url": "https://www.francemarches.com/rss/appels-offres",
            "poll_interval_minutes": 360,
            "is_active": True,
        },
        {
            "name": "Région Île-de-France",
            "source_type": SourceType.RSS,
            "description": "Appels à projets de la Région IDF",
            "url": "https://www.iledefrance.fr/appels-a-projets/feed",
            "poll_interval_minutes": 720,
            "is_active": True,
        },
        {
            "name": "Ministère de la Culture",
            "source_type": SourceType.RSS,
            "description": "Appels à projets culturels du Ministère",
            "url": "https://www.culture.gouv.fr/rss",
            "poll_interval_minutes": 720,
            "is_active": True,
        },
        
        # =============================================
        # DOMAINE ARTISTIQUE - MUSIQUE / RAP
        # =============================================
        {
            "name": "Abcdrduson - Actualités Rap",
            "source_type": SourceType.RSS,
            "description": "Média rap français - opportunités concerts, collaborations",
            "url": "https://www.abcdrduson.com/feed/",
            "poll_interval_minutes": 180,
            "is_active": True,
        },
        {
            "name": "Booska-P - Rap FR",
            "source_type": SourceType.RSS,
            "description": "Actualités rap français - événements, showcases",
            "url": "https://www.booska-p.com/feed/",
            "poll_interval_minutes": 180,
            "is_active": True,
        },
        {
            "name": "Mouv' Radio - Hip-Hop",
            "source_type": SourceType.RSS,
            "description": "Radio Mouv' - actualités hip-hop et événements",
            "url": "https://www.mouv.fr/rss",
            "poll_interval_minutes": 360,
            "is_active": True,
        },
        {
            "name": "Shotgun - Concerts & Events",
            "source_type": SourceType.HTML,
            "description": "Plateforme événements musicaux",
            "url": "https://shotgun.live/fr/events",
            "poll_interval_minutes": 360,
            "html_selectors": {
                "item_selector": ".event-card",
                "title_selector": ".event-title",
                "link_selector": "a",
                "description_selector": ".event-description",
                "date_selector": ".event-date",
            },
            "is_active": True,
        },
        {
            "name": "Dice FM - Concerts",
            "source_type": SourceType.HTML,
            "description": "Billetterie concerts - opportunités événements",
            "url": "https://dice.fm/browse/paris-fr",
            "poll_interval_minutes": 360,
            "html_selectors": {
                "item_selector": ".event-item",
                "title_selector": ".event-name",
                "link_selector": "a",
            },
            "is_active": True,
        },
        {
            "name": "CNM - Centre National de la Musique",
            "source_type": SourceType.RSS,
            "description": "Aides et subventions musique - Centre National",
            "url": "https://cnm.fr/feed/",
            "poll_interval_minutes": 720,
            "is_active": True,
        },
        {
            "name": "IRMA - Info Ressources Musiques Actuelles",
            "source_type": SourceType.RSS,
            "description": "Ressources professionnels de la musique",
            "url": "https://www.irma.asso.fr/spip.php?page=rss",
            "poll_interval_minutes": 720,
            "is_active": True,
        },
        
        # =============================================
        # DOMAINE ARTISTIQUE - MODE & FASHION
        # =============================================
        {
            "name": "Fédération Haute Couture",
            "source_type": SourceType.RSS,
            "description": "Actualités mode haute couture - Fashion Week, événements",
            "url": "https://fhcm.paris/feed/",
            "poll_interval_minutes": 720,
            "is_active": True,
        },
        {
            "name": "Fashion Network France",
            "source_type": SourceType.RSS,
            "description": "Actualités industrie mode - événements, partenariats",
            "url": "https://fr.fashionnetwork.com/rss",
            "poll_interval_minutes": 360,
            "is_active": True,
        },
        {
            "name": "Vogue France",
            "source_type": SourceType.RSS,
            "description": "Mode, beauté, culture - événements fashion",
            "url": "https://www.vogue.fr/rss",
            "poll_interval_minutes": 360,
            "is_active": True,
        },
        {
            "name": "L'Officiel",
            "source_type": SourceType.RSS,
            "description": "Magazine mode - événements, défilés",
            "url": "https://www.lofficiel.com/rss",
            "poll_interval_minutes": 360,
            "is_active": True,
        },
        {
            "name": "Mode en France",
            "source_type": SourceType.HTML,
            "description": "Portail mode française - salons, événements",
            "url": "https://www.modeenfrance.org/actualites",
            "poll_interval_minutes": 720,
            "html_selectors": {
                "item_selector": "article",
                "title_selector": "h2",
                "link_selector": "a",
            },
            "is_active": True,
        },
        
        # =============================================
        # ÉVÉNEMENTIEL & CULTURE
        # =============================================
        {
            "name": "Télérama Sortir",
            "source_type": SourceType.RSS,
            "description": "Événements culturels - concerts, expos, spectacles",
            "url": "https://www.telerama.fr/rss/sortir.xml",
            "poll_interval_minutes": 360,
            "is_active": True,
        },
        {
            "name": "Time Out Paris",
            "source_type": SourceType.RSS,
            "description": "Événements Paris - culture, sorties",
            "url": "https://www.timeout.fr/paris/rss",
            "poll_interval_minutes": 360,
            "is_active": True,
        },
        {
            "name": "SACEM - Aides et Programmes",
            "source_type": SourceType.RSS,
            "description": "Aides SACEM pour événements musicaux",
            "url": "https://www.sacem.fr/rss",
            "poll_interval_minutes": 720,
            "is_active": True,
        },
        {
            "name": "Cultura Paris",
            "source_type": SourceType.HTML,
            "description": "Événements culturels Paris",
            "url": "https://www.paris.fr/evenements",
            "poll_interval_minutes": 360,
            "html_selectors": {
                "item_selector": ".event-card",
                "title_selector": ".event-title",
                "link_selector": "a",
                "date_selector": ".event-date",
            },
            "is_active": True,
        },
        
        # =============================================
        # EMAIL - À CONFIGURER PAR L'UTILISATEUR
        # =============================================
        {
            "name": "Boîte Mail Appels d'Offres",
            "source_type": SourceType.EMAIL,
            "description": "Scan automatique des emails d'appels d'offres - Configurez vos identifiants Gmail",
            "email_folder": "INBOX",
            "poll_interval_minutes": 15,
            "is_active": False,  # Désactivé par défaut - à configurer
        },
        {
            "name": "Newsletter Events & Mode",
            "source_type": SourceType.EMAIL,
            "description": "Newsletters événementielles et mode",
            "email_folder": "NEWSLETTERS",
            "poll_interval_minutes": 30,
            "is_active": False,  # Désactivé par défaut
        },
    ]
    
    for source_data in sources:
        existing = db.query(SourceConfig).filter(
            SourceConfig.name == source_data["name"]
        ).first()
        
        if not existing:
            source = SourceConfig(**source_data)
            db.add(source)
            print(f"  ✓ Source ajoutée: {source_data['name']}")
    
    db.commit()
    print(f"\n✅ {len(sources)} sources configurées (marchés publics, rap, mode, événementiel)")


def seed_scoring_rules(db):
    """Create default scoring rules"""
    rules = [
        # Urgency rules
        {
            "name": "urgency_7_days",
            "rule_type": RuleType.URGENCY,
            "description": "Deadline dans moins de 7 jours",
            "condition_type": "deadline_days",
            "condition_value": {"operator": "lt", "value": 7},
            "points": 6,
            "label": "⚡ Deadline < 7 jours",
            "priority": 100,
        },
        {
            "name": "urgency_14_days",
            "rule_type": RuleType.URGENCY,
            "description": "Deadline dans moins de 14 jours",
            "condition_type": "deadline_days",
            "condition_value": {"operator": "lt", "value": 14},
            "points": 4,
            "label": "📅 Deadline < 14 jours",
            "priority": 90,
        },
        {
            "name": "urgency_30_days",
            "rule_type": RuleType.URGENCY,
            "description": "Deadline dans moins de 30 jours",
            "condition_type": "deadline_days",
            "condition_value": {"operator": "lt", "value": 30},
            "points": 2,
            "label": "📆 Deadline < 30 jours",
            "priority": 80,
        },
        # Event fit rules
        {
            "name": "event_fit_high",
            "rule_type": RuleType.EVENT_FIT,
            "description": "Mots-clés événementiel fort",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["privatisation", "lieu", "production événement", 
                            "scénographie", "technique", "régie", "événementiel"]
            },
            "points": 3,
            "label": "🎯 Fit événementiel fort",
            "priority": 70,
        },
        {
            "name": "event_fit_tender",
            "rule_type": RuleType.EVENT_FIT,
            "description": "Marché public / consultation",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["appel d'offres", "consultation", "marché public", "mapa"]
            },
            "points": 3,
            "label": "📋 Marché public",
            "priority": 70,
        },
        {
            "name": "event_fit_medium",
            "rule_type": RuleType.EVENT_FIT,
            "description": "Partenariat / sponsoring",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["partenariat", "sponsor", "brand content", "naming"]
            },
            "points": 2,
            "label": "🤝 Partenariat/Sponsoring",
            "priority": 60,
        },
        # =============================================
        # RÈGLES SPÉCIFIQUES MUSIQUE / RAP
        # =============================================
        {
            "name": "music_concert",
            "rule_type": RuleType.EVENT_FIT,
            "description": "Opportunité concert / showcase",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["concert", "showcase", "première partie", "tournée", 
                            "festival", "live", "scène", "booking", "date"]
            },
            "points": 4,
            "label": "🎤 Concert/Showcase",
            "priority": 75,
        },
        {
            "name": "music_rap_hiphop",
            "rule_type": RuleType.EVENT_FIT,
            "description": "Événement rap / hip-hop",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["rap", "hip-hop", "hiphop", "hip hop", "trap", "drill",
                            "freestyle", "open mic", "battle", "slam", "mc", "dj set"]
            },
            "points": 5,
            "label": "🎵 Rap/Hip-Hop",
            "priority": 80,
        },
        {
            "name": "music_production",
            "rule_type": RuleType.EVENT_FIT,
            "description": "Production musicale / studio",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["production", "beatmaker", "studio", "enregistrement",
                            "featuring", "feat", "collab", "collaboration"]
            },
            "points": 3,
            "label": "🎹 Production",
            "priority": 65,
        },
        {
            "name": "music_label",
            "rule_type": RuleType.VALUE,
            "description": "Label / Maison de disques",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["label", "maison de disques", "sony", "universal", "warner",
                            "indépendant", "distribution", "édition musicale"]
            },
            "points": 3,
            "label": "💿 Label/Distribution",
            "priority": 60,
        },
        # =============================================
        # RÈGLES SPÉCIFIQUES MODE / FASHION
        # =============================================
        {
            "name": "fashion_event",
            "rule_type": RuleType.EVENT_FIT,
            "description": "Événement mode / défilé",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["défilé", "fashion week", "collection", "présentation",
                            "runway", "catwalk", "showroom", "lookbook"]
            },
            "points": 4,
            "label": "👗 Défilé/Fashion",
            "priority": 75,
        },
        {
            "name": "fashion_collab",
            "rule_type": RuleType.EVENT_FIT,
            "description": "Collaboration mode / égérie",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["égérie", "ambassadeur", "campagne", "shooting",
                            "collaboration", "collab", "capsule", "collection capsule"]
            },
            "points": 4,
            "label": "🌟 Collab Mode",
            "priority": 70,
        },
        {
            "name": "fashion_brand",
            "rule_type": RuleType.VALUE,
            "description": "Grande marque mode",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["lvmh", "kering", "chanel", "dior", "louis vuitton",
                            "balenciaga", "givenchy", "ysl", "gucci", "hermès", "prada"]
            },
            "points": 5,
            "label": "💎 Grande Marque",
            "priority": 80,
        },
        {
            "name": "fashion_streetwear",
            "rule_type": RuleType.EVENT_FIT,
            "description": "Streetwear / Urban fashion",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["streetwear", "sneakers", "drop", "release", "pop-up",
                            "urban", "street style", "hypebeast", "limited edition"]
            },
            "points": 3,
            "label": "🔥 Streetwear",
            "priority": 65,
        },
        # =============================================
        # RÈGLES ÉVÉNEMENTIEL GÉNÉRAL
        # =============================================
        {
            "name": "event_venue",
            "rule_type": RuleType.EVENT_FIT,
            "description": "Lieu / Venue prestigieux",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["zénith", "accorhotel arena", "olympia", "bercy",
                            "stade de france", "palais", "château", "musée"]
            },
            "points": 3,
            "label": "🏟️ Lieu prestigieux",
            "priority": 60,
        },
        {
            "name": "event_media",
            "rule_type": RuleType.VALUE,
            "description": "Couverture média",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["interview", "presse", "média", "couverture",
                            "article", "reportage", "documentaire"]
            },
            "points": 2,
            "label": "📺 Média",
            "priority": 50,
        },
        # Quality rules
        {
            "name": "quality_link",
            "rule_type": RuleType.QUALITY,
            "description": "Lien principal présent",
            "condition_type": "has_field",
            "condition_value": {"fields": ["url_primary"]},
            "points": 2,
            "label": "🔗 Lien disponible",
            "priority": 50,
        },
        {
            "name": "quality_contact",
            "rule_type": RuleType.QUALITY,
            "description": "Contact détecté",
            "condition_type": "has_field",
            "condition_value": {"fields": ["contact_email", "contact_phone"]},
            "points": 2,
            "label": "📞 Contact détecté",
            "priority": 50,
        },
        # Value rules
        {
            "name": "value_budget",
            "rule_type": RuleType.VALUE,
            "description": "Budget mentionné",
            "condition_type": "has_field",
            "condition_value": {"fields": ["budget_amount"]},
            "points": 2,
            "label": "💰 Budget mentionné",
            "priority": 40,
        },
        {
            "name": "value_institution",
            "rule_type": RuleType.VALUE,
            "description": "Institution / Grande organisation",
            "condition_type": "organization_type",
            "condition_value": {
                "keywords": ["ministère", "région", "département", "mairie", 
                            "ville de", "métropole", "communauté"]
            },
            "points": 2,
            "label": "🏛️ Institution",
            "priority": 40,
        },
        # Penalty rules
        {
            "name": "penalty_no_info",
            "rule_type": RuleType.PENALTY,
            "description": "Pas de deadline ni de lien",
            "condition_type": "missing_fields",
            "condition_value": {"fields": ["deadline_at", "url_primary"]},
            "points": -4,
            "label": "⚠️ Infos manquantes",
            "priority": 30,
        },
        {
            "name": "penalty_promo",
            "rule_type": RuleType.PENALTY,
            "description": "Contenu promotionnel",
            "condition_type": "keywords",
            "condition_value": {
                "keywords": ["newsletter", "inscrivez-vous", "abonnez-vous", 
                            "suivez-nous", "promo", "soldes"]
            },
            "points": -2,
            "label": "📢 Contenu promo",
            "priority": 20,
        },
    ]
    
    for rule_data in rules:
        existing = db.query(ScoringRule).filter(
            ScoringRule.name == rule_data["name"]
        ).first()
        
        if not existing:
            rule = ScoringRule(**rule_data)
            db.add(rule)
    
    db.commit()
    print("Scoring rules seeded successfully")


def seed_database():
    """Run all seed functions"""
    print("Starting database seeding...")
    
    db = SessionLocal()
    try:
        seed_users(db)
        seed_sources(db)
        seed_scoring_rules(db)
        print("Database seeding completed!")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Alias for backward compatibility
main = seed_database


if __name__ == "__main__":
    main()
