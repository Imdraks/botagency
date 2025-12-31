# Radarapp iOS

Application iOS native pour Radarapp - Détection d'opportunités artistiques propulsée par l'IA.

## 🎯 Fonctionnalités

### Onglets principaux
- **Opportunités** - Liste des opportunités avec recherche, filtres et scoring IA
- **Dossiers** - Analyses IA détaillées sur des entités (artistes, organisations)
- **Nouvelle collecte** - Ajout de sources (RSS, HTML, Email, API)
- **Historique** - Historique des analyses d'artistes avec analyse par lot

### Design
- **Liquid Glass UI** - Design iOS 26 avec effets de verre et flou
- **Mode sombre** - Support natif du mode sombre
- **Accessibilité** - Support complet de VoiceOver et Dynamic Type

### Technique
- **Offline-first** - Cache local avec SwiftData pour utilisation hors-ligne
- **Stale-while-revalidate** - Affichage immédiat du cache puis mise à jour
- **Pull-to-refresh** - Actualisation par glissement
- **Pagination infinie** - Chargement progressif des données

## 🏗 Architecture

```
ios/
├── Radarapp/
│   ├── RadarappApp.swift          # Point d'entrée, AppState
│   ├── Info.plist                 # Configuration de l'app
│   │
│   ├── App/
│   │   ├── RootView.swift         # Navigation racine
│   │   │
│   │   ├── Components/
│   │   │   └── GlassComponents.swift    # Composants Liquid Glass
│   │   │
│   │   └── Views/
│   │       ├── Auth/
│   │       │   └── LoginView.swift
│   │       │
│   │       ├── Opportunities/
│   │       │   ├── OpportunitiesView.swift
│   │       │   └── OpportunityDetailView.swift
│   │       │
│   │       ├── Dossiers/
│   │       │   ├── DossiersView.swift
│   │       │   └── DossierDetailView.swift
│   │       │
│   │       ├── Collection/
│   │       │   └── NewCollectionView.swift
│   │       │
│   │       └── History/
│   │           └── CollectionHistoryView.swift
│   │
│   └── Core/
│       ├── Environment.swift      # Configuration DEV/PROD
│       │
│       ├── Models/
│       │   ├── Models.swift       # Modèles Codable
│       │   └── CachedModels.swift # Modèles SwiftData
│       │
│       └── Services/
│           ├── AuthService.swift       # Authentification + Keychain
│           ├── NetworkService.swift    # Couche réseau async/await
│           ├── NetworkMonitor.swift    # Surveillance connectivité
│           └── StorageService.swift    # Cache SwiftData
│
├── Configuration/
│   └── Config.xcconfig            # Variables de build
│
└── Radarapp.xcodeproj/
```

## 🔧 Configuration

### Prérequis
- Xcode 16+
- iOS 17.0+
- Swift 6

### Installation

1. Ouvrir le projet dans Xcode :
```bash
open ios/Radarapp.xcodeproj
```

2. Configurer le Team ID dans `Config.xcconfig` :
```
DEVELOPMENT_TEAM = VOTRE_TEAM_ID
```

3. Configurer l'environnement :
   - **DEV** : pointe vers `localhost:8000`
   - **PROD** : pointe vers `radarapp.fr`

### Build

```bash
# Debug (DEV)
xcodebuild -scheme "Radarapp-DEV" -configuration Debug

# Release (PROD)
xcodebuild -scheme "Radarapp-PROD" -configuration Release
```

## 📱 Screens

### Login
- Authentification email/mot de passe
- Sign in with Apple
- Sign in with Google
- Animation de fond gradient

### Opportunités
- Liste avec cards Liquid Glass
- Score badge coloré (vert/bleu/orange/rouge)
- Filtres par statut, score, deadline
- Tri par score, date, budget
- Recherche en temps réel

### Détail Opportunité
- Header avec score et statut
- Actions rapides (Intéressé, Candidater, IA)
- Sections : Description, Contact, Documents, Preuves
- Partage et export

### Dossiers
- Liste avec indicateurs de statut (pending, processing, ready)
- Badge de confiance IA
- Filtres par statut

### Détail Dossier
- Onglets : Résumé, Timeline, Contacts, Sources
- Brief court et long (IA)
- Contacts classés par pertinence
- Timeline des événements

### Nouvelle Collecte
- Sélection du type : RSS, HTML, Email, API
- Configuration spécifique par type
- Options : fréquence, scoring auto, déduplication

### Historique
- Statistiques : artistes, score moyen, cachet total
- Analyse individuelle d'artiste
- Analyse par lot (batch)
- Export CSV

## 🔐 Authentification

Tokens stockés dans Keychain :
- `access_token` : JWT pour les requêtes API
- `refresh_token` : Pour renouvellement automatique

Refresh automatique sur 401 avec retry de la requête originale.

## 💾 Cache Offline

SwiftData pour le stockage local :
- `CachedOpportunity` - Opportunités avec query de recherche
- `CachedDossier` - Dossiers IA
- `CachedCollection` - Collections/Sources
- `UserPreferences` - Préférences utilisateur

Expiration configurable (5 min DEV, 15 min PROD).

## 🌐 Networking

- `URLSession` avec `async/await`
- Retry automatique avec backoff exponentiel
- Annulation de requêtes (debounce recherche)
- Gestion centralisée des erreurs
- Décodage JSON avec snake_case → camelCase

## 🎨 Composants UI

### GlassComponents.swift
- `GlassBackground` - Fond avec effet verre
- `GlassCard` - Carte avec effet verre
- `GlassButton` - Bouton primaire/secondaire
- `GlassTextField` - Champ de saisie
- `ScoreBadge` - Badge de score coloré
- `StatusBadge` - Badge de statut
- `SkeletonView` - Placeholder de chargement
- `EmptyStateView` - État vide avec action

## 📊 API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/auth/login` | POST | Connexion |
| `/auth/refresh` | POST | Refresh token |
| `/users/me` | GET | Profil utilisateur |
| `/opportunities` | GET | Liste opportunités |
| `/opportunities/{id}` | GET | Détail opportunité |
| `/opportunities/{id}/status` | PATCH | Changer statut |
| `/dossiers` | GET | Liste dossiers |
| `/dossiers` | POST | Créer dossier |
| `/sources` | GET | Liste sources |
| `/sources` | POST | Créer source |
| `/sources/validate` | POST | Valider URL |
| `/artist-history` | GET | Historique analyses |
| `/intelligence/artist-analysis` | POST | Analyser artiste |

## 🧪 Tests

```bash
# Tests unitaires
xcodebuild test -scheme "Radarapp" -destination "platform=iOS Simulator,name=iPhone 15"

# Tests UI
xcodebuild test -scheme "Radarapp-UITests" -destination "platform=iOS Simulator,name=iPhone 15"
```

## 📦 Déploiement

### TestFlight
1. Archive via Xcode (Product → Archive)
2. Upload vers App Store Connect
3. Distribuer via TestFlight

### App Store
1. Configurer les métadonnées dans App Store Connect
2. Soumettre pour review
3. Release

## 📄 Licence

Propriétaire - Tous droits réservés
