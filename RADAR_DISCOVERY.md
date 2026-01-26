# 🔍 Radar Discovery - Documentation

## Vue d'ensemble

**Radar Discovery** est un moteur IA de détection d'artistes émergents à fort potentiel. L'objectif : **identifier les artistes AVANT qu'ils n'explosent** pour permettre aux bookers/agents de les réserver à des tarifs avantageux.

---

## 📊 Métriques analysées

L'utilisateur entre les données suivantes :

| Métrique | Description |
|----------|-------------|
| **Nom de l'artiste** | Obligatoire |
| **Auditeurs mensuels Spotify** | Nombre actuel d'auditeurs |
| **Followers Spotify** | Abonnés sur Spotify |
| **Followers réseaux sociaux** | Total Instagram, TikTok, etc. |
| **Genres** | Hip-hop, afro, pop, etc. |
| **Historique auditeurs** | Les 6 derniers mois (ex: `10000, 15000, 25000, 40000, 55000, 80000`) |

---

## ⚡ Signaux de découverte (DiscoverySignal)

Le moteur détecte automatiquement ces **signaux précurseurs** d'un breakout :

| Signal | Description | Déclencheur |
|--------|-------------|-------------|
| `VIRAL_GROWTH` | Croissance virale | +50%/mois ou plus |
| `SOCIAL_SURGE` | Explosion réseaux sociaux | Accélération > 20% |
| `PLAYLIST_BOOST` | Placement playlist majeur | Événement détecté |
| `COLLAB_BOOST` | Featuring impactant | Événement détecté |
| `LABEL_SIGNING` | Signature label | Événement détecté |
| `MEDIA_BUZZ` | Buzz presse/médias | Événement détecté |
| `AWARD_NOMINATION` | Nomination prix | Événement détecté |

---

## 📈 Patterns de croissance détectés

Le système analyse l'historique pour identifier ces **patterns** :

| Pattern | Description | Impact |
|---------|-------------|--------|
| `hockey_stick` | Croissance lente puis décollage brutal | 90% - Très fort |
| `steady_climb` | Croissance régulière et constante | 70% |
| `spike` | Pic soudain (+100%+) | 85% |
| `accelerating` | Croissance qui s'accélère | 80% |

---

## 🎯 Score de potentiel (0-100)

Le score est calculé ainsi :

```
Score = 30 (base)
       + Vélocité (max 30 pts)
       + Accélération (max 15 pts)
       + Signaux (max 15 pts)
       + Patterns (max 10 pts)
       + Bonus sweet spot (5 pts si 10K-100K auditeurs)
       - Pénalité si déjà établi (>500K)
```

### Niveaux de potentiel :

| Score | Niveau | Label |
|-------|--------|-------|
| 90-100 | `EXPLOSIVE` | 🚀 Explosif |
| 70-89 | `HIGH` | ⭐ Élevé |
| 50-69 | `PROMISING` | 💫 Prometteur |
| 30-49 | `MODERATE` | 📊 Modéré |
| <30 | `LOW` | 📉 Faible |

---

## 🎲 Probabilité de breakout

Calcul basé sur :
- Score de potentiel / 2 (base)
- +20% si `VIRAL_GROWTH`
- +15% si `PLAYLIST_BOOST` ou `LABEL_SIGNING`
- +20% si pattern `hockey_stick`
- +10% si pattern `accelerating`

**Maximum: 95%**

---

## ⏰ Estimation du timing de breakout

Le système calcule combien de mois pour atteindre 100K auditeurs :

| Estimation | Délai |
|------------|-------|
| `1-3 mois` | Imminent |
| `3-6 mois` | Court terme |
| `6-12 mois` | Moyen terme |
| `1-2 ans` | Long terme |
| `Long terme (2+ ans)` | Patience requise |

---

## 💰 Estimation des cachets

### Cachet actuel (basé sur auditeurs) :

| Auditeurs | Cachet de base |
|-----------|----------------|
| < 5K | 300€ |
| 5K-20K | 800€ |
| 20K-50K | 2 000€ |
| 50K-100K | 4 000€ |
| 100K-250K | 8 000€ |
| 250K-500K | 15 000€ |
| > 500K | 25 000€ |

*Multiplicateur ×1.5 si vélocité ≥ 50%*

### Cachet futur (6-12 mois) :
Projection basée sur la croissance et probabilité de breakout.

---

## 💡 Conseils booking générés

| Niveau | Conseil |
|--------|---------|
| **Explosif** | 🔥 BOOK MAINTENANT - Tarifs vont exploser. Fenêtre très courte. |
| **Élevé** | ⚡ Book rapidement - Prix avantageux actuellement. |
| **Prometteur** | 👀 Bon timing pour négocier. Surveiller 2-3 mois. |
| **Modéré** | 🤔 Potentiel à confirmer. Attendre signaux. |
| **Faible** | ⏳ Pas prioritaire. |

---

## 🖥️ Interface utilisateur

L'interface affiche :

1. **Formulaire d'analyse** - Entrée des métriques
2. **Jauge de potentiel** - Barre colorée 0-100%
3. **Métriques clés** - Auditeurs, croissance, accélération, timing
4. **Probabilité de breakout** - Barre de progression
5. **Signaux détectés** - Badges colorés
6. **Patterns de croissance** - Cartes avec confiance et impact
7. **Pourquoi surveiller** - Liste des raisons
8. **Comparaison cachets** - Actuel vs Futur (+X%)
9. **Conseil booking** - Recommandation actionnable

---

## � Architecture : Discovery vs Enrichment

### ⚠️ Point important

Il y a **2 systèmes différents** dans Radar :

### 1. Discovery (page /discovery) - Analyse manuelle

**Le système actuel NE RECHERCHE PAS automatiquement l'artiste.**

L'utilisateur doit **entrer manuellement** les données :
- Nom de l'artiste
- Auditeurs mensuels Spotify
- Followers Spotify
- Followers réseaux sociaux
- Historique des auditeurs

```
Frontend (formulaire) → API /ai/discover → analyze_for_potential() → Résultat
```

**Le moteur `ArtistDiscoveryEngine` fait uniquement du calcul/analyse, pas de recherche.**

### 2. Enrichment Service - Recherche automatique (autre système)

Il existe un **système d'enrichissement** qui peut rechercher les données automatiquement :

| Provider | Données récupérées | Méthode |
|----------|-------------------|---------|
| **Spotify API** | Genres, followers, popularity, albums | API officielle (spotipy) |
| **Viberate** | Monthly listeners, YouTube, Instagram, TikTok | Web scraping |
| **Wikidata** | Infos biographiques | API |
| **Label Resolver** | Label actuel | Déduction depuis albums |

#### Flux d'enrichissement :

```python
# backend/app/enrichment/service.py

class ArtistEnrichmentService:
    async def enrich(spotify_artist_input: str):
        # 1. Spotify API → genres, followers, popularity
        spotify_data = await self.spotify_provider.get(spotify_id)
        
        # 2. Viberate (web scraping) → monthly listeners, social stats
        viberate_data = await self.viberate_provider.get(spotify_id, artist_name)
        
        # 3. Wikidata → infos supplémentaires
        wikidata = await self.wikidata_provider.get(artist_name)
        
        return EnrichedArtistData(...)
```

#### Recherche Viberate (web scraping) :

```python
# backend/app/enrichment/providers/viberate.py

class ViberateProvider:
    BASE_URL = "https://www.viberate.com"
    
    async def _search_artist(artist_name: str):
        # 1. Cherche sur https://www.viberate.com/search?q={artist_name}
        # 2. Parse le HTML pour trouver le profil
        # 3. Récupère les stats depuis la page profil
        
    async def _search_artist_by_spotify_id(spotify_id: str):
        # Essaie l'URL directe: https://www.viberate.com/artist/{spotify_id}
```

### 🔮 Évolution possible : Intégration Discovery + Enrichment

Actuellement, **Discovery n'utilise pas Enrichment**. Pour automatiser :

```
Utilisateur entre "Tiakola"
       ↓
1. Recherche Spotify par nom → spotify_id
       ↓
2. Enrichment Service → toutes les données
       ↓
3. Discovery Engine → analyse potentiel
       ↓
Résultat complet automatique
```

---

## 📁 Fichiers sources

### Discovery (analyse)
- **Backend**: `backend/app/intelligence/artist_discovery_engine.py`
- **Frontend**: `frontend/src/app/discovery/page.tsx`
- **API Endpoint**: `POST /ai/discover`

### Enrichment (recherche données)
- **Service principal**: `backend/app/enrichment/service.py`
- **Provider Spotify**: `backend/app/enrichment/providers/spotify.py`
- **Provider Viberate**: `backend/app/enrichment/providers/viberate.py`
- **Provider Wikidata**: `backend/app/enrichment/providers/wikidata.py`

---

## 🚀 Exemple d'utilisation

```json
{
  "artist_name": "Tiakola",
  "monthly_listeners": 50000,
  "spotify_followers": 20000,
  "social_followers": 100000,
  "genres": ["hip-hop", "afro"],
  "historical_listeners": [10000, 15000, 25000, 40000, 55000, 80000]
}
```

**Résultat attendu** : Détection du pattern `hockey_stick`, signal `VIRAL_GROWTH`, score de potentiel élevé, conseil de booker rapidement.

---

*Documentation générée le 26 janvier 2026*
