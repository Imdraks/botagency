# Radar 🎯

**Plateforme de gestion pour agences de production** - Gérez vos projets, clients, livrables et équipes depuis une interface moderne et sécurisée.

![Version](https://img.shields.io/badge/version-2.0-blue)
![License](https://img.shields.io/badge/license-Proprietary-red)

## ✨ Fonctionnalités

### 🎬 Gestion de Production
- **Projets** : Création, suivi, deadlines, statuts (Actif, En pause, Bloqué, Terminé)
- **Clients** : Base de données clients avec contacts et historique
- **Livrables** : Suivi des livrables par projet avec statuts de validation
- **Tâches** : Attribution, priorités, deadlines, assignation d'équipe

### 📁 Intégration Google Workspace
- **Google Drive** : Création automatique d'arborescence projet
  - 00_Assets, 01_Brief, 02_Production, 03_Postprod, 04_Exports, etc.
- **Google Docs** : Génération de briefs depuis template
- **Google Calendar** : Sync des deadlines et événements

### 👥 Multi-Tenancy
- **Workspaces** : Isolation complète des données par organisation
- **Équipes** : Gestion des membres et rôles par workspace
- **Invitations** : Système d'invitation par email

### 🔐 Sécurité Avancée
- **Authentification**
  - Email/Password avec validation forte
  - SSO Google & Apple
  - 2FA (TOTP) avec codes de backup
- **Protection contre les attaques**
  - Rate limiting (brute force)
  - Détection SQL injection & XSS
  - Détection backdoors & reverse shells
  - Honeypots (pièges pour attaquants)
  - HTTPS forcé (HSTS)
- **RBAC** : Admin, Manager, Member, Viewer

### 📊 Dashboard & Analytics
- Vue d'ensemble des projets actifs
- Tâches du jour et validations en attente
- Activité récente
- Statistiques par client/projet

## 🛠️ Stack Technique

| Composant | Technologie |
|-----------|-------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI, Python 3.11, SQLAlchemy 2.0 |
| **Base de données** | PostgreSQL 15 |
| **Cache** | Redis |
| **Auth** | JWT, OAuth 2.0, TOTP |
| **Reverse Proxy** | Nginx |
| **Conteneurs** | Docker, Docker Compose |

## 📁 Structure du Projet

```
radar/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/            # Endpoints REST
│   │   ├── core/           # Config, sécurité, middlewares
│   │   ├── db/             # Models SQLAlchemy, migrations
│   │   ├── services/       # Google Workspace, etc.
│   │   └── schemas/        # Pydantic schemas
│   ├── alembic/            # Migrations DB
│   └── requirements.txt
├── frontend/               # Application Next.js
│   ├── src/
│   │   ├── app/           # Pages (App Router)
│   │   ├── components/    # Composants UI
│   │   ├── lib/           # API client, utils
│   │   └── store/         # State management
│   └── package.json
├── docker/
│   └── nginx/             # Config Nginx
├── docker-compose.yml      # Développement
└── docker-compose.prod.yml # Production
```

## 🚀 Installation

### Prérequis

- Docker & Docker Compose
- Node.js 18+ (développement frontend)
- Python 3.11+ (développement backend)

### Démarrage Rapide (Windows)

```bash
# Cloner le repo
git clone https://github.com/Imdraks/radar.git
cd radar

# Lancer l'installation
.\install.bat

# Démarrer en développement
.\dev.bat
```

### Démarrage Manuel

1. **Configuration**

```bash
cp .env.example .env
# Éditer .env avec vos credentials
```

2. **Lancer les services**

```bash
docker-compose up -d
```

3. **Initialiser la base de données**

```bash
docker-compose exec backend alembic upgrade head
```

4. **Accéder à l'application**

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

## ⚙️ Configuration

### Variables d'Environnement Principales

```env
# Application
APP_ENV=production
SECRET_KEY=your-super-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/radar

# Redis
REDIS_URL=redis://localhost:6379/0

# Google OAuth (SSO + Drive)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx

# Email (invitations)
RESEND_API_KEY=re_xxx
```

### Google Workspace Integration

1. Créer un projet dans [Google Cloud Console](https://console.cloud.google.com)
2. Activer les APIs : Drive, Docs, Sheets, Calendar
3. Configurer OAuth 2.0 avec les scopes appropriés
4. Ajouter les credentials dans `.env`

## 🔒 Sécurité

### Protections Intégrées

| Protection | Description |
|------------|-------------|
| Rate Limiting | 5 req/min login, 100 req/min API |
| SQL Injection | Détection et blocage des patterns |
| XSS | Headers CSP, sanitization inputs |
| CSRF | Tokens de validation |
| Backdoors | Détection reverse shells, command injection |
| Path Traversal | Blocage `../` et variantes |
| File Upload | Validation extensions et contenu |
| Honeypots | Pièges pour détecter les attaquants |

### Exigences Mot de Passe

- Minimum 8 caractères
- Au moins 1 majuscule
- Au moins 1 minuscule
- Au moins 1 chiffre
- Au moins 1 caractère spécial (!@#$%^&*)

## 🌐 Production

### Déploiement

```bash
# Sur le serveur
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### SSL/HTTPS

Certificats SSL via Let's Encrypt ou configuration manuelle dans `docker/nginx/nginx.prod.conf`.

### Domaine

L'application est déployée sur `radarapp.fr`.

## 📝 API Endpoints

### Authentification
- `POST /api/v1/auth/login` - Connexion
- `POST /api/v1/auth/logout` - Déconnexion
- `POST /api/v1/auth/refresh` - Rafraîchir token
- `GET /api/v1/sso/google/login` - SSO Google

### Projets
- `GET /api/v1/agency/projects` - Liste des projets
- `POST /api/v1/agency/projects` - Créer un projet
- `GET /api/v1/agency/projects/{id}` - Détail projet
- `PATCH /api/v1/agency/projects/{id}` - Modifier projet

### Assets
- `GET /api/v1/assets` - Liste des assets
- `POST /api/v1/assets` - Créer un asset
- `POST /api/v1/drive/upload` - Upload vers Drive

### Tâches
- `GET /api/v1/agency/tasks` - Liste des tâches
- `POST /api/v1/agency/tasks` - Créer une tâche
- `PATCH /api/v1/agency/tasks/{id}` - Modifier tâche

## 🧪 Tests

```bash
# Backend
docker-compose exec backend pytest

# Frontend
cd frontend && npm test
```

## 👥 Rôles Utilisateurs

| Rôle | Permissions |
|------|-------------|
| **Admin** | Accès total, gestion utilisateurs, configuration |
| **Manager** | Gestion projets, clients, équipe |
| **Member** | Création/édition projets et tâches |
| **Viewer** | Lecture seule |

## 📄 Licence

**Propriétaire** - Usage interne uniquement. Tous droits réservés.

---

Développé avec ❤️ par NIDPOOL
