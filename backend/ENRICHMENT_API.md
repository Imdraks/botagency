# Artist Data Enrichment API

## 🎯 Architecture Overview

Solution modulaire production-ready pour enrichir les données d'artistes avec :
- **Monthly Listeners** (Apify Actor)
- **Genres, Followers, Popularity** (Spotify Web API)
- **Principal Label** (Apify ou Spotify Albums)
- **Management** (Wikidata)

---

## 📐 Architecture Modulaire

### Providers
Chaque source de données = 1 provider indépendant :

```
providers/
├── base.py              # BaseProvider avec retry, cache, circuit breaker
├── monthly_listeners.py # Apify Actor
├── spotify.py           # Spotify Web API
├── label_resolver.py    # Résolution du label principal
└── wikidata.py          # Management via SPARQL
```

### Service Layer
`service.py` orchestre tous les providers et coordonne l'enrichissement.

### API Layer
`api/enrichment.py` expose les endpoints REST.

---

## 🚀 Endpoints API

### 1. MVP - Enrichissement simple

**POST /enrichment/artists/enrich**
```json
{
  "spotify_artist_id": "2pvfGvbL4mouaDY9ZSwUmv",
  "force_refresh": false
}
```

**Response:**
```json
{
  "artist": {
    "id": "2pvfGvbL4mouaDY9ZSwUmv",
    "name": "Gims",
    "spotify_id": "2pvfGvbL4mouaDY9ZSwUmv",
    "spotify_url": "https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv"
  },
  "monthly_listeners": {
    "value": 18500000,
    "provider": "apify:augeas/spotify-monthly-listeners",
    "retrieved_at": "2025-12-23T10:30:00Z",
    "confidence": 1.0,
    "evidence": ["Apify run: abc123xyz"]
  },
  "spotify": {
    "genres": ["french hip hop", "rap francais"],
    "followers_total": 8500000,
    "popularity": 82
  },
  "labels": {
    "principal": "Play Two",
    "method": "latest_release",
    "retrieved_at": "2025-12-23T10:30:01Z",
    "evidence": [
      {
        "release_id": "abc123",
        "release_name": "Les derniers salopards",
        "release_date": "2024-10-04",
        "label": "Play Two"
      }
    ]
  },
  "management": {
    "value": "Renversant Artists",
    "provider": "wikidata",
    "retrieved_at": "2025-12-23T10:30:02Z",
    "confidence": 1.0,
    "evidence": {
      "wikidata_entity": "Q3098697",
      "match_property": "P1902",
      "management_property": "P1037"
    }
  },
  "notes": []
}
```

---

### 2. PROD - GET avec refresh optionnel

**GET /enrichment/artists/{artist_id}?refresh=true**

Récupère les données enrichies (cache ou fresh).

---

### 3. PROD - Refresh explicite

**POST /enrichment/artists/{artist_id}/refresh**

Force le refresh (bypass cache).

---

### 4. PROD - Batch enrichment

**POST /enrichment/artists/batch/enrich**
```json
{
  "artist_ids": [
    "2pvfGvbL4mouaDY9ZSwUmv",
    "7bXgB6jMjp9ATFy66eO08Z",
    "1Xyo4u8uXC1ZmMpatF05PJ"
  ],
  "force_refresh": false
}
```

Retourne un array de `EnrichedArtistData`.

**Limite: 50 artistes par batch** pour éviter les timeouts.

---

### 5. PROD - Monitoring

**GET /enrichment/metrics**

Métriques par provider :
- Success/failure rate
- Cache hit rate
- Latence moyenne
- Circuit breaker state

```json
{
  "monthly_listeners": {
    "provider": "MonthlyListenersProvider",
    "requests": 150,
    "success_rate": 0.96,
    "failure_rate": 0.04,
    "cache_hit_rate": 0.65,
    "avg_latency": 2.3,
    "circuit_breaker_state": "closed"
  },
  "spotify": { ... },
  "wikidata": { ... }
}
```

---

## ⚙️ Configuration

### Variables d'environnement

Ajouter dans `.env` :

```bash
# Apify
ENRICHMENT_APIFY_API_TOKEN=your_apify_token

# Cache TTLs (seconds)
ENRICHMENT_CACHE_TTL_MONTHLY_LISTENERS=3600    # 1h
ENRICHMENT_CACHE_TTL_LABELS=86400              # 24h
ENRICHMENT_CACHE_TTL_MANAGEMENT=604800         # 7 days
ENRICHMENT_CACHE_TTL_SPOTIFY_DATA=86400        # 24h

# Retry & Circuit Breaker
ENRICHMENT_MAX_RETRIES=3
ENRICHMENT_RETRY_BACKOFF_FACTOR=2.0
ENRICHMENT_CIRCUIT_BREAKER_THRESHOLD=5
ENRICHMENT_CIRCUIT_BREAKER_TIMEOUT=60

# Timeouts (seconds)
ENRICHMENT_TIMEOUT_APIFY=120
ENRICHMENT_TIMEOUT_SPOTIFY=10
ENRICHMENT_TIMEOUT_WIKIDATA=15

# Label Resolution
ENRICHMENT_LABEL_RESOLUTION_METHOD=latest_release  # or most_frequent
ENRICHMENT_LABEL_MOST_FREQUENT_COUNT=20

# Batch Processing
ENRICHMENT_BATCH_SIZE=50
ENRICHMENT_BATCH_CONCURRENCY=5
```

### Obtenir le token Apify

1. Créer un compte sur https://apify.com
2. Aller dans Settings → Integrations
3. Copier le "Personal API token"
4. Ajouter dans `.env` : `ENRICHMENT_APIFY_API_TOKEN=...`

---

## 🏗️ Data Flow

```
User Request
    ↓
API Endpoint
    ↓
ArtistEnrichmentService
    ↓
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│                 │                 │                 │                 │
MonthlyListeners  SpotifyProvider   LabelResolver    WikidataProvider
(Apify)           (Web API)         (Logic)          (SPARQL)
│                 │                 │                 │
Cache Check       Cache Check       -                 Cache Check
│                 │                 │                 │
Retry Logic       Retry Logic       -                 Retry Logic
│                 │                 │                 │
Circuit Breaker   Circuit Breaker   -                 Circuit Breaker
│                 │                 │                 │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
                              ↓
                    EnrichedArtistData
                              ↓
                      JSON Response
```

---

## 🛡️ Production Features

### 1. Cache avec TTL différenciés
- Monthly listeners: 1h (change souvent)
- Labels: 24h (stable)
- Management: 7 jours (quasi-statique)

### 2. Retry avec exponential backoff
- 3 tentatives par défaut
- Backoff: 2^attempt secondes
- Logs détaillés

### 3. Circuit Breaker
- 5 échecs consécutifs → OPEN
- 60s timeout → HALF_OPEN
- 1 succès → CLOSED

### 4. Logs structurés
```python
logger.info(f"MonthlyListenersProvider: Success for {artist_id} (2.3s)")
logger.error(f"WikidataProvider: Error for {artist_id}: Timeout")
```

### 5. Métriques en temps réel
- Taux de succès par provider
- Cache hit rate
- Latence moyenne
- État des circuit breakers

---

## 📦 Installation

### 1. Dépendances

Ajouter dans `requirements.txt` :
```txt
apify-client==1.7.1
httpx==0.27.0
```

Installer :
```bash
pip install apify-client httpx
```

### 2. Enregistrer l'API

Dans `backend/app/main.py` :
```python
from app.api import enrichment

app.include_router(enrichment.router, prefix="/api")
```

### 3. Configuration

Copier les variables d'environnement dans `.env`.

### 4. Redémarrer

```bash
docker-compose restart backend
```

---

## 🧪 Tests

### Test unitaire - Monthly Listeners

```python
import asyncio
from app.enrichment.config import EnrichmentConfig
from app.enrichment.providers.monthly_listeners import MonthlyListenersProvider

async def test_monthly_listeners():
    config = EnrichmentConfig(apify_api_token="your_token")
    provider = MonthlyListenersProvider(config)
    
    result = await provider.fetch("2pvfGvbL4mouaDY9ZSwUmv")
    print(result)

asyncio.run(test_monthly_listeners())
```

### Test complet - Service

```python
import asyncio
from app.enrichment.service import ArtistEnrichmentService
from app.enrichment.config import EnrichmentConfig

async def test_enrichment():
    config = EnrichmentConfig(
        apify_api_token="your_apify_token",
        spotify_client_id="your_spotify_id",
        spotify_client_secret="your_spotify_secret"
    )
    
    service = ArtistEnrichmentService(
        config=config,
        spotify_client_id=config.spotify_client_id,
        spotify_client_secret=config.spotify_client_secret
    )
    
    result = await service.enrich("https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv")
    print(result.model_dump_json(indent=2))

asyncio.run(test_enrichment())
```

### Test API - cURL

```bash
# Enrich artist
curl -X POST http://localhost:8000/api/enrichment/artists/enrich \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "spotify_url": "https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv"
  }'

# Get with refresh
curl -X GET "http://localhost:8000/api/enrichment/artists/2pvfGvbL4mouaDY9ZSwUmv?refresh=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Batch enrich
curl -X POST http://localhost:8000/api/enrichment/artists/batch/enrich \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_ids": ["2pvfGvbL4mouaDY9ZSwUmv", "7bXgB6jMjp9ATFy66eO08Z"]
  }'

# Metrics
curl -X GET http://localhost:8000/api/enrichment/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔄 Mode Batch vs Temps Réel

### Temps Réel (MVP)
**Use case:** Recherche d'artiste par l'utilisateur

```python
# Single artist enrichment
result = await service.enrich("2pvfGvbL4mouaDY9ZSwUmv")
```

**Avantages:**
- Réponse immédiate
- Cache utilisé si disponible
- Idéal pour UI interactive

### Batch (PROD)
**Use case:** Refresh nocturne de 1000 artistes

```python
# Batch with Apify optimization
results = await service.enrich_batch([
    "id1", "id2", "id3", ...  # up to 50
])
```

**Avantages:**
- 1 seul run Apify pour N artistes
- Coût optimisé
- Throughput élevé

**Recommandation PROD:**
- Utiliser Celery pour batches > 50 artistes
- Queue Redis avec rate limiting
- Cron job quotidien

---

## 📊 Label Resolution - Détails

### Méthode 1: latest_release (défaut)
Utilise le label de la sortie la plus récente.

**Exemple:**
```
Releases:
1. "Album 2024" - 2024-10-04 - Label: "Play Two"
2. "Single 2024" - 2024-08-15 - Label: "Def Jam"
3. "Album 2023" - 2023-05-12 - Label: "Sony"

→ Principal: "Play Two"
```

### Méthode 2: most_frequent
Compte les labels sur les N dernières sorties (N=20 par défaut).

**Exemple:**
```
Releases (20 dernières):
- "Play Two": 12 occurrences
- "Def Jam": 5 occurrences
- "Sony": 3 occurrences

→ Principal: "Play Two"
```

**Configuration:**
```bash
ENRICHMENT_LABEL_RESOLUTION_METHOD=most_frequent
ENRICHMENT_LABEL_MOST_FREQUENT_COUNT=30
```

### Déduplication
Gère automatiquement :
- Deluxe editions
- Remastered versions
- Multi-marchés

**Stratégie:** Unique par `(name_normalized, release_date)`.

---

## 🌐 Wikidata - Management

### SPARQL Query
```sparql
SELECT ?entity ?entityLabel ?manager ?managerLabel WHERE {
  ?entity wdt:P1902 "2pvfGvbL4mouaDY9ZSwUmv".
  OPTIONAL { ?entity wdt:P1037 ?manager }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr". }
}
```

### Propriétés
- **P1902:** Spotify artist ID (matching)
- **P1037:** director/manager (management)

### Fallback
Si aucun résultat → `value: null`, `confidence: 0.0`

---

## 🚦 État du Circuit Breaker

| État | Description | Action |
|------|-------------|--------|
| **CLOSED** | Normal | Toutes les requêtes passent |
| **OPEN** | Trop d'échecs | Toutes les requêtes échouent immédiatement |
| **HALF_OPEN** | Test | 1 requête test, si succès → CLOSED |

**Seuil:** 5 échecs consécutifs
**Timeout:** 60 secondes

---

## 💡 MVP vs PROD

### Version MVP (Simple)
✅ Endpoint POST `/artists/enrich`
✅ Retry basique (3x)
✅ Logs simples
✅ Pas de cache
✅ Synchrone

**Use case:** Prototype, tests, low volume

### Version PROD (Robuste)
✅ GET + POST + Batch endpoints
✅ Cache Redis avec TTL différenciés
✅ Circuit breaker par provider
✅ Métriques en temps réel
✅ Retry avec exponential backoff
✅ Logs structurés
✅ Background jobs (Celery)
✅ Rate limiting
✅ Monitoring (Prometheus/Grafana)

**Use case:** Production, high volume, SLA

---

## 📈 Scaling Recommendations

### Pour > 1000 artistes/jour

1. **Implémenter cache Redis**
```python
# Dans providers/base.py
async def _get_from_cache(self, key: str):
    return await self.cache.get(key)

async def _set_in_cache(self, key: str, value: Dict):
    await self.cache.setex(key, self.ttl, json.dumps(value))
```

2. **Utiliser Celery pour batch jobs**
```python
# workers/enrichment_tasks.py
@celery_app.task
def enrich_artist_task(artist_id: str):
    result = await service.enrich(artist_id)
    # Store in DB
```

3. **Rate limiting Apify**
Apify a des limites de concurrence. Utiliser un semaphore :
```python
semaphore = asyncio.Semaphore(5)  # Max 5 concurrent
```

4. **Monitoring avec Prometheus**
```python
from prometheus_client import Counter, Histogram

enrichment_requests = Counter('enrichment_requests_total', 'Total requests')
enrichment_latency = Histogram('enrichment_latency_seconds', 'Latency')
```

---

## 🔍 Exemple Complet - Gims

**Input:**
```
https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv
```

**Output:**
```json
{
  "artist": {
    "id": "2pvfGvbL4mouaDY9ZSwUmv",
    "name": "Gims",
    "spotify_id": "2pvfGvbL4mouaDY9ZSwUmv",
    "spotify_url": "https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv"
  },
  "monthly_listeners": {
    "value": 18500000,
    "provider": "apify:augeas/spotify-monthly-listeners",
    "retrieved_at": "2025-12-23T10:30:00.123456Z",
    "confidence": 1.0,
    "evidence": ["Apify run: xR7k9PqL2mN4"]
  },
  "spotify": {
    "genres": ["french hip hop", "pop urbaine", "rap francais"],
    "followers_total": 8500000,
    "popularity": 82
  },
  "labels": {
    "principal": "Play Two",
    "method": "latest_release",
    "retrieved_at": "2025-12-23T10:30:01.234567Z",
    "evidence": [
      {
        "release_id": "7bXgB6jMjp9ATFy66eO08Z",
        "release_name": "Les derniers salopards",
        "release_date": "2024-10-04",
        "label": "Play Two"
      },
      {
        "release_id": "abc123xyz",
        "release_name": "Immortel",
        "release_date": "2021-09-03",
        "label": "Play Two"
      }
    ]
  },
  "management": {
    "value": "Renversant Artists",
    "provider": "wikidata",
    "retrieved_at": "2025-12-23T10:30:02.345678Z",
    "confidence": 1.0,
    "evidence": {
      "wikidata_entity": "Q3098697",
      "match_property": "P1902",
      "management_property": "P1037"
    }
  },
  "notes": []
}
```

---

## 🎯 Résumé

### Architecture
- **4 providers** modulaires et indépendants
- **1 service** orchestrateur
- **1 API** avec 5 endpoints

### Features PROD
✅ Cache différencié par TTL
✅ Retry avec backoff exponentiel
✅ Circuit breaker per-provider
✅ Métriques en temps réel
✅ Logs structurés
✅ Batch optimisé (Apify)
✅ Evidence trail complet

### Next Steps
1. Installer dépendances (`apify-client`, `httpx`)
2. Configurer `.env` avec token Apify
3. Enregistrer l'API dans `main.py`
4. Tester avec Gims
5. Implémenter cache Redis
6. Ajouter background jobs (Celery)
7. Monitoring (Prometheus)

---

**Documentation générée le 23/12/2025**
