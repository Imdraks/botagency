"""Script to add music/event sources to the database"""
from app.db.session import SessionLocal
from app.db.models.source import SourceConfig
from app.db.models.opportunity import SourceType

db = SessionLocal()

# Liste des sources à ajouter
sources = [
    {
        'name': 'CNM - Centre National de la Musique',
        'source_type': SourceType.RSS,
        'description': 'Actualités et appels à projets du Centre National de la Musique',
        'url': 'https://cnm.fr/feed/',
        'is_active': True,
        'poll_interval_minutes': 360
    },
    {
        'name': 'IRMA - Actualités Musique',
        'source_type': SourceType.RSS,
        'description': 'Centre d\'information et de ressources pour les musiques actuelles',
        'url': 'https://www.irma.asso.fr/spip.php?page=backend',
        'is_active': True,
        'poll_interval_minutes': 360
    },
    {
        'name': 'Tsugi Magazine',
        'source_type': SourceType.RSS,
        'description': 'Magazine musique électronique et cultures urbaines',
        'url': 'https://www.tsugi.fr/feed/',
        'is_active': True,
        'poll_interval_minutes': 360
    },
    {
        'name': 'Les Inrocks',
        'source_type': SourceType.RSS,
        'description': 'Actualités musicales et culturelles',
        'url': 'https://www.lesinrocks.com/feed/',
        'is_active': True,
        'poll_interval_minutes': 360
    },
    {
        'name': 'Trax Magazine',
        'source_type': SourceType.RSS,
        'description': 'Magazine électronique - festivals et événements',
        'url': 'https://www.traxmag.com/feed/',
        'is_active': True,
        'poll_interval_minutes': 360
    },
    {
        'name': 'Culturebox - Concerts',
        'source_type': SourceType.RSS,
        'description': 'Actualités concerts et festivals de France Télévisions',
        'url': 'https://www.francetvinfo.fr/culture/musique/rss',
        'is_active': True,
        'poll_interval_minutes': 360
    },
    {
        'name': 'Telerama - Musique',
        'source_type': SourceType.RSS,
        'description': 'Critiques et actualités musicales',
        'url': 'https://www.telerama.fr/rss/musique.xml',
        'is_active': True,
        'poll_interval_minutes': 360
    },
    {
        'name': 'Resident Advisor - France',
        'source_type': SourceType.RSS,
        'description': 'Événements électroniques en France',
        'url': 'https://ra.co/xml/features.xml',
        'is_active': True,
        'poll_interval_minutes': 360
    },
]

added = 0
for s in sources:
    existing = db.query(SourceConfig).filter(SourceConfig.name == s['name']).first()
    if not existing:
        source = SourceConfig(**s)
        db.add(source)
        added += 1
        name = s['name']
        print(f'✅ Ajouté: {name}')
    else:
        name = s['name']
        print(f'⏭️  Existe déjà: {name}')

db.commit()
db.close()
print(f'\n🎉 Total ajouté: {added} sources')
