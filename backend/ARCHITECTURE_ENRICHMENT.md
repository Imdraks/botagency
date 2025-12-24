# 🏗️ Architecture - Artist Enrichment API

## Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│                    Artist Search / Display                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI)                           │
│  /enrichment/artists/enrich                                      │
│  /enrichment/artists/{id}                                        │
│  /enrichment/artists/{id}/refresh                                │
│  /enrichment/artists/batch/enrich                                │
│  /enrichment/metrics                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              SERVICE LAYER (Orchestration)                       │
│           ArtistEnrichmentService                                │
│  - Coordonne les providers                                       │
│  - Gère le cache                                                 │
│  - Agrège les résultats                                          │
└─────┬───────────┬───────────┬───────────┬────────────────────────┘
      │           │           │           │
      ▼           ▼           ▼           ▼
┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Monthly   │ │ Spotify  │ │  Label   │ │  Wikidata    │
│ Listeners │ │ Provider │ │ Resolver │ │  Provider    │
│ Provider  │ │          │ │          │ │              │
│ (Apify)   │ │ (Web API)│ │ (Logic)  │ │  (SPARQL)    │
└─────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘
      │            │            │               │
      │ Retry      │ Retry      │               │ Retry
      │ Circuit    │ Circuit    │               │ Circuit
      │ Breaker    │ Breaker    │               │ Breaker
      │ Cache      │ Cache      │               │ Cache
      │            │            │               │
      ▼            ▼            ▼               ▼
┌──────────┐ ┌──────────┐ ┌──────────┐  ┌──────────────┐
│  Apify   │ │ Spotify  │ │ Spotify  │  │  Wikidata    │
│  Actor   │ │   API    │ │ Albums   │  │   SPARQL     │
└──────────┘ └──────────┘ └──────────┘  └──────────────┘
```

---

## Modules & Responsabilités

### 1. **API Layer** (`api/enrichment.py`)
- Expose les endpoints REST
- Validation des requêtes (Pydantic)
- Authentification (JWT)
- Gestion des erreurs HTTP

**Endpoints:**
```python
POST /enrichment/artists/enrich          # MVP
GET  /enrichment/artists/{id}            # PROD
POST /enrichment/artists/{id}/refresh    # PROD
POST /enrichment/artists/batch/enrich    # PROD
GET  /enrichment/metrics                 # PROD
```

---

### 2. **Service Layer** (`enrichment/service.py`)
- Orchestration des providers
- Extraction Spotify ID depuis URL
- Agrégation des résultats
- Gestion des notes/warnings

**Responsabilités:**
```python
class ArtistEnrichmentService:
    async def enrich(artist_id) -> EnrichedArtistData
    async def enrich_batch(artist_ids) -> List[EnrichedArtistData]
    def get_metrics() -> Dict
```

---

### 3. **Provider Layer** (`enrichment/providers/`)

#### 3.1 **BaseProvider** (`base.py`)
- Pattern Template Method
- Retry avec exponential backoff
- Circuit breaker
- Cache abstraction
- Métriques par provider

**Features:**
```python
class BaseProvider:
    async def get(artist_id, force_refresh=False)
    async def _fetch_with_retry(artist_id)
    def get_metrics() -> Dict
```

#### 3.2 **MonthlyListenersProvider** (`monthly_listeners.py`)
- Apify Actor: `augeas/spotify-monthly-listeners`
- Mode single & batch
- Confidence: 1.0 (source autoritaire)

**Input:**
```json
{
  "startUrls": [
    {"url": "https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv"}
  ]
}
```

**Output:**
```json
{
  "value": 18500000,
  "provider": "apify:augeas/spotify-monthly-listeners",
  "confidence": 1.0
}
```

#### 3.3 **SpotifyProvider** (`spotify.py`)
- Spotify Web API
- Genres, Followers, Popularity
- Fallback pour labels (albums)

**Endpoints utilisés:**
```
GET /v1/artists/{id}
GET /v1/artists/{id}/albums
GET /v1/albums/{album_id}
```

#### 3.4 **LabelResolver** (`label_resolver.py`)
- Résolution du label principal
- 2 méthodes: `latest_release`, `most_frequent`
- Déduplication (deluxe, reissues)

**Logique:**
```python
# Méthode 1: Latest Release
sorted_releases = sort_by_date(releases)
principal = sorted_releases[0].label

# Méthode 2: Most Frequent
labels_count = Counter([r.label for r in releases[:20]])
principal = labels_count.most_common(1)[0][0]
```

#### 3.5 **WikidataProvider** (`wikidata.py`)
- SPARQL queries
- Matching: P1902 (Spotify artist ID)
- Management: P1037 (director/manager)

**Query:**
```sparql
SELECT ?entity ?manager ?managerLabel WHERE {
  ?entity wdt:P1902 "2pvfGvbL4mouaDY9ZSwUmv".
  OPTIONAL { ?entity wdt:P1037 ?manager }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr". }
}
```

---

## Data Models (`enrichment/models.py`)

### EnrichedArtistData (Output complet)
```python
{
  "artist": ArtistInfo,
  "monthly_listeners": MonthlyListenersData,
  "spotify": SpotifyData,
  "labels": LabelsData,
  "management": ManagementData,
  "notes": List[str]
}
```

### Evidence Trail
Chaque donnée inclut sa provenance :
```python
{
  "value": "Play Two",
  "provider": "spotify:albums",
  "retrieved_at": "2025-12-23T10:30:00Z",
  "confidence": 0.95,
  "evidence": [...]
}
```

---

## Configuration (`enrichment/config.py`)

### Variables d'environnement
```bash
# Providers
ENRICHMENT_APIFY_API_TOKEN=xxx

# Cache TTLs (seconds)
ENRICHMENT_CACHE_TTL_MONTHLY_LISTENERS=3600    # 1h
ENRICHMENT_CACHE_TTL_LABELS=86400              # 24h
ENRICHMENT_CACHE_TTL_MANAGEMENT=604800         # 7j

# Retry & Circuit Breaker
ENRICHMENT_MAX_RETRIES=3
ENRICHMENT_RETRY_BACKOFF_FACTOR=2.0
ENRICHMENT_CIRCUIT_BREAKER_THRESHOLD=5
ENRICHMENT_CIRCUIT_BREAKER_TIMEOUT=60

# Timeouts (seconds)
ENRICHMENT_TIMEOUT_APIFY=120
ENRICHMENT_TIMEOUT_SPOTIFY=10
ENRICHMENT_TIMEOUT_WIKIDATA=15
```

---

## Patterns & Best Practices

### 1. **Circuit Breaker Pattern**
Protège contre les cascades de pannes :

```python
States: CLOSED → OPEN → HALF_OPEN → CLOSED

CLOSED:     Requêtes passent normalement
OPEN:       Toutes les requêtes échouent immédiatement
HALF_OPEN:  1 requête test, si succès → CLOSED
```

### 2. **Retry avec Exponential Backoff**
```python
Attempt 1: Immediate
Attempt 2: Wait 2s (2^1)
Attempt 3: Wait 4s (2^2)
```

### 3. **Cache avec TTL différenciés**
```python
Monthly Listeners: 1h  (change souvent)
Labels:           24h  (stable)
Management:       7j   (quasi-statique)
```

### 4. **Evidence Trail**
Toute donnée inclut sa provenance pour debugging :
```python
{
  "value": 18500000,
  "provider": "apify:augeas/spotify-monthly-listeners",
  "evidence": ["Apify run: xR7k9PqL2mN4"],
  "confidence": 1.0
}
```

---

## Flow d'Exécution

### Single Artist Enrichment

```
1. User Request
   POST /enrichment/artists/enrich
   {"spotify_url": "https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv"}

2. Service Layer
   service.enrich("2pvfGvbL4mouaDY9ZSwUmv")

3. Parallel Provider Calls
   ┌─────────────────────────────────────────┐
   │ monthly_listeners_provider.get()        │
   │ spotify_provider.get()                  │
   │ spotify_provider.fetch_albums()         │
   │ wikidata_provider.get()                 │
   └─────────────────────────────────────────┘

4. Label Resolution
   label_resolver.resolve(spotify_albums)

5. Aggregation
   EnrichedArtistData(
     monthly_listeners=...,
     spotify=...,
     labels=...,
     management=...
   )

6. Response
   JSON avec toutes les données + evidence trail
```

### Batch Enrichment

```
1. Batch Request
   POST /enrichment/artists/batch/enrich
   {"artist_ids": ["id1", "id2", ..., "id50"]}

2. Apify Batch Call
   monthly_listeners_provider.fetch_batch([...])
   → 1 seul Apify run pour 50 artistes

3. Individual Provider Calls (parallel)
   for artist_id in artist_ids:
     spotify_provider.get(artist_id)
     wikidata_provider.get(artist_id)
     ...

4. Aggregation
   List[EnrichedArtistData]

5. Response
   Array JSON de tous les artistes
```

---

## Métriques & Monitoring

### Provider Metrics
```python
GET /enrichment/metrics

{
  "monthly_listeners": {
    "provider": "MonthlyListenersProvider",
    "requests": 150,
    "success_rate": 0.96,      # 96% succès
    "failure_rate": 0.04,      # 4% échec
    "cache_hit_rate": 0.65,    # 65% cache
    "avg_latency": 2.3,        # 2.3s moyenne
    "circuit_breaker_state": "closed"
  },
  "spotify": {...},
  "wikidata": {...}
}
```

### Logs Structurés
```python
INFO  - MonthlyListenersProvider: Success for 2pvfGvbL4mouaDY9ZSwUmv (2.3s)
INFO  - SpotifyProvider: Cache hit for 2pvfGvbL4mouaDY9ZSwUmv
WARN  - WikidataProvider: Retry 1/3 for 2pvfGvbL4mouaDY9ZSwUmv after 2s
ERROR - MonthlyListenersProvider: Circuit breaker opened
```

---

## Scaling & Production

### Pour > 1000 artistes/jour

1. **Cache Redis**
```python
# Actuellement: In-memory (MVP)
# Production: Redis avec pipeline

await redis.setex(
  key=f"enrichment:monthly:{artist_id}",
  time=3600,
  value=json.dumps(data)
)
```

2. **Celery Background Jobs**
```python
# Tâche Celery
@celery_app.task
def enrich_artist_task(artist_id: str):
    result = await service.enrich(artist_id)
    # Store in DB

# Cron quotidien
'refresh-top-artists': {
    'task': 'enrichment_tasks.refresh_top_artists_daily',
    'schedule': crontab(hour=2, minute=0),
}
```

3. **Rate Limiting**
```python
# Apify: Max 5 concurrent
semaphore = asyncio.Semaphore(5)

async with semaphore:
    result = await apify_client.run(...)
```

4. **Monitoring Prometheus**
```python
from prometheus_client import Counter, Histogram

enrichment_requests = Counter('enrichment_requests_total')
enrichment_latency = Histogram('enrichment_latency_seconds')
```

---

## Sécurité

### 1. **Authentication**
Tous les endpoints requièrent JWT :
```python
@router.post("/artists/enrich")
async def enrich_artist(
    request: EnrichmentRequest,
    current_user: User = Depends(get_current_user)
):
```

### 2. **Rate Limiting** (à implémenter)
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("10/minute")
@router.post("/artists/enrich")
```

### 3. **Input Validation**
```python
class EnrichmentRequest(BaseModel):
    spotify_artist_id: Optional[str]
    spotify_url: Optional[str]
    
    @validator('spotify_url')
    def validate_url(cls, v):
        if not re.match(r'spotify\.com/artist/[a-zA-Z0-9]{22}', v):
            raise ValueError('Invalid Spotify URL')
```

---

## Tests

### Unit Tests
```python
# tests/enrichment/test_providers.py
async def test_monthly_listeners_provider():
    provider = MonthlyListenersProvider(config)
    result = await provider.fetch("2pvfGvbL4mouaDY9ZSwUmv")
    assert result["value"] > 1000000
```

### Integration Tests
```python
# tests/enrichment/test_service.py
async def test_full_enrichment():
    service = ArtistEnrichmentService(config, ...)
    result = await service.enrich("2pvfGvbL4mouaDY9ZSwUmv")
    assert result.monthly_listeners.value
    assert result.labels.principal
```

### API Tests
```python
# tests/api/test_enrichment.py
def test_enrich_endpoint(client):
    response = client.post(
        "/api/v1/enrichment/artists/enrich",
        json={"spotify_artist_id": "2pvfGvbL4mouaDY9ZSwUmv"}
    )
    assert response.status_code == 200
    assert response.json()["monthly_listeners"]["value"]
```

---

## Évolutions Futures

### Phase 2
- [ ] Cache Redis distribué
- [ ] Celery background jobs
- [ ] Rate limiting par utilisateur
- [ ] Webhooks pour refresh async

### Phase 3
- [ ] GraphQL API
- [ ] WebSocket pour updates temps réel
- [ ] Machine Learning pour label prediction
- [ ] Data warehouse (BigQuery/Snowflake)

---

**Architecture v1.0 - Décembre 2025**
