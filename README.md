# Opportunities Radar 🎯

Application web de veille et qualification d'opportunités pour agences événementielles.

## 🚀 Features

- **Ingestion automatique** : emails (IMAP), RSS, scraping HTML, APIs
- **Extraction intelligente** : deadlines, budgets, contacts (NLP léger + regex)
- **Déduplication** : hash URL + similarité texte
- **Scoring configurable** : urgence, fit événementiel, qualité info
- **Pipeline CRM** : NEW → QUALIFIED → IN_PROGRESS → WON/LOST
- **Dashboard** : top opportunités, deadlines proches, stats
- **Notifications** : Discord/Slack webhooks, emails SMTP

## 📁 Structure

```
botagency/
├── backend/                 # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/            # Endpoints REST
│   │   ├── core/           # Config, auth, security
│   │   ├── db/             # Database models, migrations
│   │   ├── ingestion/      # Connecteurs (email, RSS, HTML)
│   │   ├── extraction/     # NLP, parsing
│   │   ├── scoring/        # Moteur de scoring
│   │   └── workers/        # Celery tasks
│   ├── tests/
│   ├── alembic/
│   └── requirements.txt
├── frontend/               # Next.js + TypeScript
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # UI components
│   │   ├── lib/           # Utils, API client
│   │   └── hooks/         # React hooks
│   ├── public/
│   └── package.json
├── docker/
│   ├── nginx/
│   └── ...
├── docker-compose.yml
├── docker-compose.prod.yml
└── .env.example
```

## 🛠️ Installation

### Prérequis

- Docker & Docker Compose
- Node.js 18+ (dev frontend)
- Python 3.11+ (dev backend)

### Développement

1. **Cloner et configurer**

```bash
git clone <repo>
cd botagency
cp .env.example .env
# Éditer .env avec vos credentials
```

2. **Lancer avec Docker Compose**

```bash
docker-compose up -d
```

Services :
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

3. **Initialiser la base de données**

```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.db.seed
```

### Configuration IMAP (emails newsletters)

Dans `.env` :

```env
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=newsletters@votreagence.com
IMAP_PASSWORD=app_password_here
IMAP_FOLDER=NEWSLETTERS
IMAP_USE_SSL=true
```

Pour Gmail, créer un "App Password" dans les paramètres de sécurité.

### Lancer l'ingestion manuellement

```bash
# Via API (auth requise)
curl -X POST http://localhost:8000/api/v1/ingestion/run \
  -H "Authorization: Bearer <token>"

# Via Celery task
docker-compose exec worker celery -A app.workers.celery_app call app.workers.tasks.run_all_ingestion
```

## 🔧 Configuration

### Scoring Rules

Éditer via l'interface admin ou dans `backend/config/scoring.yml` :

```yaml
rules:
  urgency:
    - condition: "deadline_days < 7"
      points: 6
      label: "Deadline < 7 jours"
    - condition: "deadline_days < 14"
      points: 4
      label: "Deadline < 14 jours"
  
  event_fit:
    - keywords: ["privatisation", "lieu", "scénographie"]
      points: 3
      label: "Fit événementiel fort"
```

### Sources

Types supportés :
- `EMAIL` : IMAP polling
- `RSS` : Flux RSS/Atom
- `HTML` : Scraping avec sélecteurs CSS
- `API` : Endpoints JSON

## 🧪 Tests

```bash
# Backend
docker-compose exec backend pytest

# Frontend
cd frontend && npm test
```

## 📊 API Documentation

Swagger UI disponible sur `/docs` une fois le backend lancé.

Endpoints principaux :
- `POST /api/v1/auth/login` - Authentification
- `GET /api/v1/opportunities` - Liste avec filtres
- `GET /api/v1/opportunities/{id}` - Détail
- `PATCH /api/v1/opportunities/{id}` - Mise à jour
- `GET /api/v1/sources` - Liste des sources
- `POST /api/v1/ingestion/run` - Lancer ingestion

## 🔐 Sécurité

- Auth JWT avec refresh tokens
- RBAC : `admin`, `bizdev`, `pm`, `viewer`
- Rate limiting sur API
- Secrets dans `.env` (jamais en repo)
- HTTPS obligatoire en prod

## 📦 Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Voir `docker/nginx/nginx.conf` pour la config reverse proxy.

## 📄 License

Propriétaire - Usage interne uniquement
