# 🚀 Quick Start - Artist Enrichment API

## Installation (5 minutes)

### 1. Installer les dépendances

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurer Apify

1. Créer un compte sur [apify.com](https://apify.com)
2. Aller dans **Settings → Integrations**
3. Copier le **Personal API token**
4. Ajouter dans votre `.env` :

```bash
ENRICHMENT_APIFY_API_TOKEN=apify_api_xxx...xxx
```

### 3. Vérifier Spotify credentials

Assurez-vous que ces variables existent dans `.env` :

```bash
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

### 4. Redémarrer le backend

```bash
# Si Docker
docker-compose restart backend

# Si local
uvicorn app.main:app --reload
```

---

## ✅ Test Rapide

### Test 1: Via script Python

```bash
cd backend
python test_enrichment_api.py
```

**Résultat attendu:**
```
🎤 Artist: Gims
🎧 Monthly Listeners: 18,500,000
🏢 Label: Play Two
👔 Management: Renversant Artists
```

### Test 2: Via cURL

```bash
curl -X POST http://localhost:8000/api/v1/enrichment/artists/enrich \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "spotify_url": "https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv"
  }'
```

### Test 3: Via Swagger UI

1. Ouvrir http://localhost:8000/docs
2. Aller dans **Artist Enrichment** → **POST /enrichment/artists/enrich**
3. Cliquer **Try it out**
4. Entrer :
```json
{
  "spotify_url": "https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv"
}
```
5. **Execute**

---

## 📊 Endpoints Disponibles

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/enrichment/artists/enrich` | POST | Enrichir 1 artiste |
| `/enrichment/artists/{id}` | GET | Récupérer données (cache) |
| `/enrichment/artists/{id}/refresh` | POST | Forcer le refresh |
| `/enrichment/artists/batch/enrich` | POST | Enrichir plusieurs (max 50) |
| `/enrichment/metrics` | GET | Métriques providers |

---

## 🎯 Cas d'Usage

### Use Case 1: Recherche artiste par utilisateur

```python
# Frontend appelle
POST /enrichment/artists/enrich
{
  "spotify_artist_id": "2pvfGvbL4mouaDY9ZSwUmv"
}

# Backend retourne
{
  "monthly_listeners": { "value": 18500000 },
  "labels": { "principal": "Play Two" },
  "management": { "value": "Renversant Artists" },
  ...
}
```

### Use Case 2: Refresh nocturne (batch)

```python
# Celery task scheduled à 2h du matin
POST /enrichment/artists/batch/enrich
{
  "artist_ids": ["id1", "id2", ..., "id50"]
}
```

### Use Case 3: Monitoring

```python
# Dashboard admin
GET /enrichment/metrics

# Retourne
{
  "monthly_listeners": {
    "success_rate": 0.96,
    "cache_hit_rate": 0.65,
    "avg_latency": 2.3
  }
}
```

---

## 🔧 Troubleshooting

### ❌ "Apify client not initialized"

**Solution:** Vérifier que `ENRICHMENT_APIFY_API_TOKEN` est dans `.env`

```bash
echo $ENRICHMENT_APIFY_API_TOKEN
```

### ❌ "Spotify API error"

**Solution:** Vérifier credentials Spotify

```bash
# Dans .env
SPOTIFY_CLIENT_ID=xxx
SPOTIFY_CLIENT_SECRET=yyy  # Doit être DIFFÉRENT du client ID
```

### ❌ "Wikidata timeout"

**Solution:** Augmenter le timeout

```bash
# Dans .env
ENRICHMENT_TIMEOUT_WIKIDATA=30
```

### ❌ "Circuit breaker open"

**Solution:** Attendre 60s ou redémarrer le service

```bash
docker-compose restart backend
```

---

## 📈 Performance

### Latences typiques

| Provider | Latence moyenne | TTL Cache |
|----------|----------------|-----------|
| Spotify API | ~0.5s | 24h |
| Apify | ~2-3s | 1h |
| Wikidata | ~1s | 7 jours |

### Optimisations

**Cache Hit Rate cible: 80%+**

Pour améliorer :
1. Augmenter les TTL
2. Pré-charger les artistes populaires
3. Utiliser Redis (implémentation future)

---

## 🎓 Prochaines Étapes

1. ✅ **Installation** - Suivre ce guide
2. ✅ **Test** - Vérifier avec Gims
3. 📝 **Intégration Frontend** - Appeler les endpoints
4. 🔄 **Batch Jobs** - Configurer Celery tasks
5. 📊 **Monitoring** - Dashboard métriques
6. 🚀 **Production** - Cache Redis + rate limiting

---

## 📚 Documentation Complète

Voir [ENRICHMENT_API.md](./ENRICHMENT_API.md) pour :
- Architecture détaillée
- Tous les providers
- Configuration avancée
- Exemples de code
- Production best practices

---

**Questions ?** Consulter la doc ou tester avec `python test_enrichment_api.py`
