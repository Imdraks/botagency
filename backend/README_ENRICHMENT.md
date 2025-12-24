# 🎵 Artist Data Enrichment API

> **Production-ready API** pour enrichir les données d'artistes avec **monthly listeners**, **labels**, **genres**, et **management** depuis **Apify**, **Spotify**, et **Wikidata**.

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Installer dépendances
pip install apify-client==1.7.1 httpx==0.27.0

# 2. Configurer Apify token
echo "ENRICHMENT_APIFY_API_TOKEN=your_token" >> .env

# 3. Tester
python test_enrichment_api.py
```

**✅ Résultat attendu:**
```
🎤 Artist: Gims
🎧 Monthly Listeners: 18,500,000
🏢 Label: Play Two
👔 Management: Renversant Artists
```

➡️ **[Guide complet de démarrage](QUICK_START_ENRICHMENT.md)**

---

## 📊 Ce que vous obtenez

### Input
```json
{
  "spotify_url": "https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv"
}
```

### Output
```json
{
  "artist": { "name": "Gims", ... },
  "monthly_listeners": { "value": 18500000, "provider": "apify", ... },
  "spotify": { "genres": ["french hip hop"], "followers": 8500000, ... },
  "labels": { "principal": "Play Two", "evidence": [...] },
  "management": { "value": "Renversant Artists", "evidence": {...} }
}
```

➡️ **[Voir JSON complet](example_response_gims.json)**

---

## 🎯 Features

### Version MVP (Simple)
- ✅ Endpoint POST `/enrichment/artists/enrich`
- ✅ Retry automatique (3x)
- ✅ Logs structurés
- ✅ Evidence trail (provenance des données)

### Version PROD (Robuste)
- ✅ **5 endpoints REST** (GET, POST, Batch, Refresh, Metrics)
- ✅ **Cache intelligent** avec TTL différenciés (1h à 7j)
- ✅ **Circuit breaker** pour fault tolerance
- ✅ **Exponential backoff** pour les retries
- ✅ **Métriques temps réel** (success rate, latence, cache hit)
- ✅ **Batch API** (jusqu'à 50 artistes)
- ✅ **Background jobs** (Celery)
- ✅ **Authentication JWT**

---

## 📡 API Endpoints

### 1. Enrich Artist
```http
POST /api/v1/enrichment/artists/enrich
{
  "spotify_artist_id": "2pvfGvbL4mouaDY9ZSwUmv"
}
```

### 2. Get Artist (with cache)
```http
GET /api/v1/enrichment/artists/2pvfGvbL4mouaDY9ZSwUmv?refresh=false
```

### 3. Force Refresh
```http
POST /api/v1/enrichment/artists/2pvfGvbL4mouaDY9ZSwUmv/refresh
```

### 4. Batch Enrich
```http
POST /api/v1/enrichment/artists/batch/enrich
{
  "artist_ids": ["id1", "id2", ..., "id50"]
}
```

### 5. Provider Metrics
```http
GET /api/v1/enrichment/metrics
```

---

## 🏗️ Architecture

### Providers Modulaires

```
Service Layer
    ↓
┌───────────┬──────────┬──────────┬──────────┐
│           │          │          │          │
Monthly     Spotify    Label      Wikidata
Listeners   Provider   Resolver   Provider
(Apify)     (Web API)  (Logic)    (SPARQL)
```

**Chaque provider inclut:**
- Retry avec exponential backoff
- Circuit breaker
- Cache avec TTL
- Métriques (success rate, latence)

➡️ **[Architecture détaillée](ARCHITECTURE_ENRICHMENT.md)**

---

## 📚 Documentation

| Document | Description | Temps de lecture |
|----------|-------------|------------------|
| **[QUICK_START_ENRICHMENT.md](QUICK_START_ENRICHMENT.md)** | Installation & premiers tests | 5 min |
| **[ENRICHMENT_API.md](ENRICHMENT_API.md)** | Documentation complète | 30 min |
| **[ARCHITECTURE_ENRICHMENT.md](ARCHITECTURE_ENRICHMENT.md)** | Patterns & design | 15 min |
| **[ENRICHMENT_RECAP.md](ENRICHMENT_RECAP.md)** | Résumé exécutif | 10 min |

---

## 🔧 Configuration

### Variables essentielles

```bash
# Apify (REQUIS)
ENRICHMENT_APIFY_API_TOKEN=apify_api_xxx

# Cache TTLs
ENRICHMENT_CACHE_TTL_MONTHLY_LISTENERS=3600    # 1h
ENRICHMENT_CACHE_TTL_LABELS=86400              # 24h
ENRICHMENT_CACHE_TTL_MANAGEMENT=604800         # 7j

# Retry & Circuit Breaker
ENRICHMENT_MAX_RETRIES=3
ENRICHMENT_CIRCUIT_BREAKER_THRESHOLD=5
ENRICHMENT_CIRCUIT_BREAKER_TIMEOUT=60

# Timeouts
ENRICHMENT_TIMEOUT_APIFY=120
ENRICHMENT_TIMEOUT_SPOTIFY=10
ENRICHMENT_TIMEOUT_WIKIDATA=15
```

➡️ **[Voir toutes les options](.env.enrichment.example)**

---

## 🧪 Tests

### Script de test Python
```bash
python test_enrichment_api.py
```

### Exemples de code
```bash
python app/enrichment/examples.py
```

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/enrichment/artists/enrich \
  -H "Content-Type: application/json" \
  -d '{"spotify_artist_id": "2pvfGvbL4mouaDY9ZSwUmv"}'
```

### Swagger UI
http://localhost:8000/docs → **Artist Enrichment**

---

## 📈 Performance

### Latences typiques

| Provider | Latence | Cache TTL | Source |
|----------|---------|-----------|--------|
| Spotify API | ~0.5s | 24h | Officiel |
| Apify | ~2-3s | 1h | Web scraping |
| Wikidata | ~1s | 7j | SPARQL |

### Métriques cibles

- **Success Rate:** >95%
- **Cache Hit Rate:** >80%
- **Avg Latency:** <3s (avec cache)

---

## 💡 Cas d'Usage

### 1. Page Artist Details
```javascript
// Frontend affiche profil artiste enrichi
const data = await enrichmentAPI.enrich(artistId)
```

### 2. Calcul Score Opportunité
```python
# Système de scoring utilise monthly listeners
score = calculate_score(
    monthly_listeners=enriched.monthly_listeners.value,
    popularity=enriched.spotify.popularity
)
```

### 3. Refresh Nocturne
```python
# Celery task @ 2 AM
refresh_top_artists_daily()  # Batch de 100 artistes
```

---

## 📦 Structure du Code

```
app/
├── api/
│   └── enrichment.py              # API endpoints
├── enrichment/
│   ├── config.py                  # Configuration
│   ├── models.py                  # Data models (Pydantic)
│   ├── service.py                 # Service orchestrator
│   ├── examples.py                # Code examples
│   └── providers/
│       ├── base.py                # BaseProvider + Circuit Breaker
│       ├── monthly_listeners.py   # Apify provider
│       ├── spotify.py             # Spotify Web API
│       ├── label_resolver.py      # Label logic
│       └── wikidata.py            # Wikidata SPARQL
└── workers/
    └── enrichment_tasks.py        # Celery background jobs
```

---

## 🔒 Sécurité & Production

### ✅ Implémenté
- JWT Authentication
- Input validation (Pydantic)
- Circuit breaker
- Retry logic
- Structured logging
- Evidence trail

### 🔜 À implémenter
- Rate limiting par user
- Redis cache distribué
- Prometheus metrics
- Load balancing

---

## 🌟 Exemples

### Exemple 1: Enrichir Gims
```python
from app.enrichment.service import ArtistEnrichmentService

result = await service.enrich("https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv")

print(f"Monthly Listeners: {result.monthly_listeners.value:,}")
print(f"Label: {result.labels.principal}")
print(f"Management: {result.management.value}")
```

### Exemple 2: Batch de 50 artistes
```python
results = await service.enrich_batch([
    "2pvfGvbL4mouaDY9ZSwUmv",  # Gims
    "7bXgB6jMjp9ATFy66eO08Z",  # Niska
    # ... 48 autres
])
```

### Exemple 3: Métriques providers
```python
metrics = service.get_metrics()

print(f"Success Rate: {metrics['monthly_listeners']['success_rate']*100:.1f}%")
print(f"Cache Hit Rate: {metrics['spotify']['cache_hit_rate']*100:.1f}%")
```

---

## 🛠️ Troubleshooting

### ❌ "Apify client not initialized"
```bash
# Solution: Vérifier token Apify dans .env
grep ENRICHMENT_APIFY_API_TOKEN .env
```

### ❌ "Spotify API error: 401"
```bash
# Solution: Vérifier que Client Secret ≠ Client ID
grep SPOTIFY .env
```

### ❌ "Circuit breaker open"
```bash
# Solution: Attendre 60s ou redémarrer
docker-compose restart backend
```

➡️ **[Guide complet de troubleshooting](QUICK_START_ENRICHMENT.md#troubleshooting)**

---

## 💰 Coûts Estimés

- **Apify:** ~$0.001/artiste = $30/mois pour 1000 artistes/jour
- **Spotify API:** Gratuit (10k req/jour)
- **Wikidata:** Gratuit
- **Infrastructure (Redis):** $10-50/mois

**Total:** ~$40-80/mois pour 1000 artistes/jour

---

## 📞 Support

### Documentation
- 📖 [Quick Start](QUICK_START_ENRICHMENT.md) - Démarrage rapide
- 📚 [API Docs](ENRICHMENT_API.md) - Documentation complète
- 🏗️ [Architecture](ARCHITECTURE_ENRICHMENT.md) - Design patterns
- 📋 [Récap](ENRICHMENT_RECAP.md) - Résumé exécutif

### Tests
- 🧪 `python test_enrichment_api.py` - Script de test
- 💡 `app/enrichment/examples.py` - Code examples
- 🌐 http://localhost:8000/docs - Swagger UI

### Fichiers
- 📝 [example_response_gims.json](example_response_gims.json) - Exemple JSON complet
- ⚙️ [.env.enrichment.example](.env.enrichment.example) - Template config

---

## ✅ Checklist Installation

- [ ] Installer `apify-client` et `httpx`
- [ ] Obtenir token Apify (apify.com)
- [ ] Ajouter `ENRICHMENT_APIFY_API_TOKEN` dans `.env`
- [ ] Vérifier Spotify credentials
- [ ] Redémarrer backend
- [ ] Tester avec `python test_enrichment_api.py`
- [ ] Vérifier `/docs` pour Swagger UI
- [ ] Intégrer dans le frontend

---

## 🎯 Résumé

### Ce que vous avez
✅ API complète pour enrichissement artistes
✅ 4 sources de données (Apify, Spotify, Wikidata)
✅ Production-ready (retry, circuit breaker, cache, metrics)
✅ Documentation exhaustive (100+ pages)
✅ Tests inclus

### Prochaines étapes
1. **Installer** les dépendances
2. **Configurer** le token Apify
3. **Tester** avec le script Python
4. **Intégrer** dans votre frontend
5. **Monitorer** avec les métriques

---

**Version 1.0 - Décembre 2025**

*Built with ❤️ for production use*
