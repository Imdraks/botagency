# 🚀 DISCOVERY V3 - Spécification Technique

> **Version**: 3.0  
> **Date**: 26 janvier 2026  
> **Auteur**: Lead Engineer  
> **Statut**: SPEC TECHNIQUE (prêt pour implémentation)

---

## 📋 Table des matières

1. [Objectifs Produit](#-objectifs-produit)
2. [Scope](#-scope)
3. [Backend - Architecture](#-backend--architecture)
   - [Data Model](#a-data-model-db)
   - [Pipeline Enrichment](#b-pipeline-enrichment-worker-async)
   - [Cache / Performance](#c-cache--performance)
   - [Discovery Feed Generator](#d-discovery-feed-generator-job-planifié)
   - [API Endpoints](#e-api-endpoints)
   - [Security / RBAC](#f-security--rbac)
4. [Frontend - Architecture](#-frontend--architecture)
   - [Page Découverte](#a-page-découverte-discovery)
   - [Page Comparaison](#b-page-comparaison-comparison)
   - [State Management](#c-state-management)
   - [Empty States](#d-empty-states)
5. [Conventions Produit](#-conventions-produit)
6. [Critères d'Acceptation](#-critères-dacceptation)
7. [Livrables](#-livrables)

---

## 🎯 Objectifs Produit

> **NON NÉGOCIABLES**

| # | Objectif | Règle |
|---|----------|-------|
| 1 | **Découverte passive** | Ne doit JAMAIS déclencher du scraping juste en étant ouverte. Consomme uniquement des données "computed / cached". |
| 2 | **Comparaison passive** | Ne déclenche JAMAIS du scraping (sauf bouton explicite "Rafraîchir" → job async). |
| 3 | **Recherche = Job async** | Recherche artiste (URL Viberate/Spotify/nom) lance un job async avec étapes visibles: `MATCH → VIBERATE → SPOTIFY → COMPUTE`. |
| 4 | **Optimisation serveur** | Cache TTL, jobs, pas de recalcul live. |
| 5 | **UI décisionnelle** | "Outil de décision", pas "dashboard expérimental". |

---

## 📦 Scope

### ✅ Inclus

| Couche | Éléments |
|--------|----------|
| **Frontend** | Pages `/discovery` et `/comparison` + composants (cards, filtres, watchlist actions, queue jobs) |
| **Backend** | Endpoints REST, modèles DB, queue worker, cache, règles anti-doublons |

### ❌ Exclus

- Refonte page "Artistes" (déjà traitée)
- Refonte Core/Business
- Mobile UI

---

## 🔧 Backend — Architecture

### A) Data Model (DB)

#### 1. `ArtistEntity`

> Entité principale artiste

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK workspace |
| `canonical_name` | VARCHAR | Nom officiel |
| `normalized_name` | VARCHAR | Nom normalisé (lowercase, sans accents) |
| `viberate_url` | VARCHAR (nullable) | URL profil Viberate |
| `spotify_artist_id` | VARCHAR (nullable) | ID Spotify (22 chars) |
| `instagram_url` | VARCHAR (nullable) | Lien Instagram |
| `tiktok_url` | VARCHAR (nullable) | Lien TikTok |
| `youtube_url` | VARCHAR (nullable) | Lien YouTube |
| `created_at` | TIMESTAMP | Date création |
| `updated_at` | TIMESTAMP | Date modification |
| `last_enriched_at` | TIMESTAMP (nullable) | Dernier enrichissement |
| `data_quality` | ENUM | `HIGH` \| `MEDIUM` \| `LOW` |
| `last_quality_reason` | TEXT/JSON | Raison du niveau qualité |
| `is_deleted` | BOOLEAN | Soft delete |

**Index**: `workspace_id`, `normalized_name`, `spotify_artist_id`

---

#### 2. `ArtistSnapshotRaw`

> Stockage debug + audit des données brutes

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | PK |
| `artist_id` | UUID | FK ArtistEntity |
| `source` | ENUM | `VIBERATE` \| `SPOTIFY` \| `SOCIAL` |
| `fetched_at` | TIMESTAMP | Date du fetch |
| `ttl_expires_at` | TIMESTAMP | Expiration TTL |
| `status` | ENUM | `OK` \| `PARTIAL` \| `FAILED` |
| `error_code` | VARCHAR (nullable) | `429`, `PARSER_CHANGED`, `NOT_FOUND`, `TIMEOUT`... |
| `raw_payload_ref` | VARCHAR | Référence S3/Minio ou JSON compressé |
| `parser_version` | VARCHAR | Ex: `viberate_parser_v3` |

**Index**: `artist_id`, `source`, `fetched_at DESC`

---

#### 3. `ArtistComputedMetrics`

> **Données consommées par l'UI** (source unique de vérité)

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | PK |
| `artist_id` | UUID | FK ArtistEntity |
| `computed_at` | TIMESTAMP | Date du calcul |
| `score` | INTEGER | 0-100 |
| `timing_bucket` | ENUM | `IMMINENT` \| `1_3M` \| `3_6M` \| `6_12M` \| `LONG` |
| `recommendation` | ENUM | `BOOK` \| `WATCHLIST` \| `IGNORE` |
| `drivers` | JSONB | `[{label, value, impact: +/-}]` |
| `penalties` | JSONB | `[{label, value, impact: -}]` |
| `monthly_listeners_series` | JSONB | `[{date, value}]` (6 mois) |
| `velocity` | FLOAT | Taux de croissance |
| `acceleration` | FLOAT | Accélération croissance |
| `signals` | JSONB | `[{type, strength, evidenceUrl?, detectedAt?, source}]` |
| `patterns` | JSONB | `[{type, confidence}]` |
| `fee_estimate_min` | INTEGER | Cachet estimé min (€) |
| `fee_estimate_max` | INTEGER | Cachet estimé max (€) |
| `confidence_index` | INTEGER (nullable) | 0-100 |
| `data_quality` | ENUM | `HIGH` \| `MEDIUM` \| `LOW` |
| `last_updated_by_source` | JSONB | `{viberate: timestamp, spotify: timestamp}` |
| `version` | VARCHAR | Version algo (ex: `v3.1`) |

**Index**: `artist_id`, `computed_at DESC`  
**Contrainte**: Un seul computed "actif" par artiste (le plus récent)

---

#### 4. `DiscoveryCandidate`

> Table matérialisée pour le feed Découverte (pré-calculé)

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK workspace |
| `artist_id` | UUID | FK ArtistEntity |
| `candidate_type` | ENUM | `RECOMMENDED` \| `TRENDING` |
| `rank_score` | FLOAT | Score de classement |
| `reasons` | JSONB | Top 2 drivers (court) |
| `computed_at` | TIMESTAMP | Date génération |
| `ttl_expires_at` | TIMESTAMP | Expiration |
| `segment_key` | VARCHAR (nullable) | Clé segmentation optionnelle |

**Index**: `workspace_id`, `candidate_type`, `rank_score DESC`  
**TTL**: 30-120 min selon volume

---

#### 5. `ComparisonList`

> Shortlists de comparaison

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK workspace |
| `name` | VARCHAR | Nom de la liste |
| `created_by` | UUID | FK User |
| `created_at` | TIMESTAMP | Date création |
| `updated_at` | TIMESTAMP | Date modification |

---

#### 6. `ComparisonListItem`

> Items dans une shortlist

| Colonne | Type | Description |
|---------|------|-------------|
| `list_id` | UUID | FK ComparisonList |
| `artist_id` | UUID | FK ArtistEntity |
| `added_at` | TIMESTAMP | Date ajout |
| `order_index` | INTEGER | Ordre d'affichage |

**PK composée**: `(list_id, artist_id)`

---

#### 7. `EnrichmentJob`

> Tracking UI des jobs d'enrichissement

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK workspace |
| `requested_by` | UUID | FK User |
| `input_type` | ENUM | `VIBERATE_URL` \| `SPOTIFY_URL` \| `NAME` |
| `input_value` | VARCHAR | Valeur entrée |
| `artist_id` | UUID (nullable) | FK ArtistEntity (après MATCH) |
| `status` | ENUM | `QUEUED` \| `RUNNING` \| `PARTIAL` \| `FAILED` \| `DONE` |
| `current_step` | ENUM | `MATCH` \| `VIBERATE` \| `SPOTIFY` \| `COMPUTE` |
| `progress_pct` | INTEGER | 0-100 |
| `error_code` | VARCHAR (nullable) | Code erreur |
| `error_message` | TEXT (nullable) | Message erreur user-friendly |
| `created_at` | TIMESTAMP | Date création |
| `updated_at` | TIMESTAMP | Date modification |
| `logs_ref` | VARCHAR (nullable) | Référence logs détaillés (admin only) |

**Index**: `workspace_id`, `status`, `created_at DESC`

---

### B) Pipeline Enrichment (Worker Async)

> Orchestration idempotente en 4 étapes

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE ENRICHMENT                                │
├──────────┬──────────────┬──────────────┬──────────────┬─────────────────┤
│  INPUT   │   1. MATCH   │  2. VIBERATE │  3. SPOTIFY  │   4. COMPUTE    │
│          │   (0-25%)    │   (25-50%)   │   (50-75%)   │    (75-100%)    │
├──────────┼──────────────┼──────────────┼──────────────┼─────────────────┤
│URL Vibe  │ Extract ID   │ Fetch+Parse  │ Fetch API    │ Calculate       │
│URL Spot  │ Extract ID   │ Search name  │ Fetch API    │ metrics         │
│NAME      │ Search/Match │ Fetch+Parse  │ Fetch API    │ → Upsert        │
└──────────┴──────────────┴──────────────┴──────────────┴─────────────────┘
```

#### Étape 1: MATCH (Identity Resolution)

```python
def step_match(job: EnrichmentJob):
    """
    Résolution d'identité - Anti-doublons
    """
    if job.input_type == "VIBERATE_URL":
        # Extract canonical artist page id + name
        artist_id, name = parse_viberate_url(job.input_value)
        
    elif job.input_type == "SPOTIFY_URL":
        # Extract spotifyArtistId
        spotify_id = parse_spotify_url(job.input_value)
        
    elif job.input_type == "NAME":
        # 1. Chercher dans index interne
        existing = search_internal_index(job.input_value, job.workspace_id)
        if existing:
            return existing
        
        # 2. Sinon, search Viberate → retourner candidates
        candidates = search_viberate(job.input_value)
        if len(candidates) > 1:
            return {"status": "NEED_SELECTION", "candidates": candidates}
    
    # Créer ou merger ArtistEntity (anti-doublon)
    artist = upsert_artist_entity(...)
    job.artist_id = artist.id
    return artist
```

#### Étape 2: VIBERATE FETCH + PARSE

```python
def step_viberate(job: EnrichmentJob):
    """
    Web scraping Viberate avec rate limit
    """
    # Rate limit: max 1 req/2s, retry avec backoff
    page_html = fetch_with_retry(
        url=job.viberate_url,
        rate_limit="1/2s",
        max_retries=3,
        backoff="exponential"
    )
    
    # Parse données
    data = parse_viberate_page(page_html, parser_version="v3")
    
    # Stocker snapshot raw
    snapshot = ArtistSnapshotRaw(
        artist_id=job.artist_id,
        source="VIBERATE",
        status="OK" if data.complete else "PARTIAL",
        raw_payload_ref=store_payload(data.raw),
        parser_version="viberate_parser_v3"
    )
    
    # Update ArtistEntity avec liens sociaux
    update_artist_links(job.artist_id, data.social_links)
    
    # Extraire spotify_artist_id si présent
    if data.spotify_link:
        job.spotify_artist_id = extract_spotify_id(data.spotify_link)
```

#### Étape 3: SPOTIFY FETCH + PARSE

```python
def step_spotify(job: EnrichmentJob):
    """
    API Spotify officielle
    """
    if not job.spotify_artist_id:
        # Pas de lien Spotify trouvé
        return {"status": "PARTIAL", "reason": "NO_SPOTIFY_LINK"}
    
    # Fetch via spotipy
    artist_data = spotify_client.artist(job.spotify_artist_id)
    
    # Monthly listeners series (si API dispo)
    listeners_history = fetch_listeners_history(job.spotify_artist_id)
    
    # Store snapshot
    snapshot = ArtistSnapshotRaw(
        artist_id=job.artist_id,
        source="SPOTIFY",
        status="OK",
        raw_payload_ref=store_payload(artist_data)
    )
```

#### Étape 4: COMPUTE

```python
def step_compute(job: EnrichmentJob):
    """
    Calcul des métriques finales
    """
    # Lire dernières sources OK/PARTIAL
    viberate_snapshot = get_latest_snapshot(job.artist_id, "VIBERATE")
    spotify_snapshot = get_latest_snapshot(job.artist_id, "SPOTIFY")
    
    # Calculer métriques
    metrics = compute_artist_metrics(
        viberate_data=viberate_snapshot.data,
        spotify_data=spotify_snapshot.data if spotify_snapshot else None
    )
    
    # Déterminer data quality
    data_quality = assess_data_quality(viberate_snapshot, spotify_snapshot)
    
    # Upsert computed metrics
    upsert_computed_metrics(
        artist_id=job.artist_id,
        metrics=metrics,
        data_quality=data_quality,
        last_updated_by_source={
            "viberate": viberate_snapshot.fetched_at,
            "spotify": spotify_snapshot.fetched_at if spotify_snapshot else None
        }
    )
    
    job.status = "DONE"
    job.progress_pct = 100
```

---

### C) Cache / Performance

> **Règle**: Ne JAMAIS recalculer compute à la demande UI

#### TTL Recommandés

| Donnée | TTL | Justification |
|--------|-----|---------------|
| VIBERATE snapshot | 12-24h | Rate limit strict |
| SPOTIFY monthly listeners | 6-12h | Données moins volatiles |
| Computed metrics | Après refresh ou expiration sources | Cohérence |
| DiscoveryCandidate | 30-120 min | Selon volume workspace |

#### Cache Redis

```python
# Clés Redis recommandées

# Feed discovery (paginé)
"discovery:{workspace_id}:{mode}:{filters_hash}:page_{n}" -> JSON
TTL: 60-180s

# Computed metrics par artiste
"computed:{artist_id}" -> JSON
TTL: 300s (stale-while-revalidate)

# Jobs actifs
"jobs:{workspace_id}:active" -> SET[job_id]
```

#### Rate Limiting

| Domaine | Limite | Concurrence |
|---------|--------|-------------|
| Viberate | 1 req / 2s | Max 2 workers |
| Spotify API | 100 req / min | Max 5 workers |
| Global | - | 2-5 workers total |

---

### D) Discovery Feed Generator (Job Planifié)

> Cronjob périodique (toutes les 1-6h selon usage)

```python
@celery.task
def generate_discovery_candidates():
    """
    Génère les feeds RECOMMENDED et TRENDING
    """
    for workspace in get_active_workspaces():
        # Sélectionner artistes avec computed récents
        artists = get_artists_with_fresh_metrics(
            workspace_id=workspace.id,
            max_age_hours=48
        )
        
        # === RECOMMENDED ===
        recommended = []
        for artist in artists:
            rank = calculate_recommended_rank(
                score=artist.metrics.score,
                timing=artist.metrics.timing_bucket,
                sweet_spot=(10000 <= artist.monthly_listeners <= 100000),
                data_quality=artist.metrics.data_quality
            )
            recommended.append((artist, rank))
        
        recommended.sort(key=lambda x: x[1], reverse=True)
        
        # === TRENDING ===
        trending = []
        for artist in artists:
            rank = calculate_trending_rank(
                velocity=artist.metrics.velocity,
                acceleration=artist.metrics.acceleration,
                signals=artist.metrics.signals
            )
            trending.append((artist, rank))
        
        trending.sort(key=lambda x: x[1], reverse=True)
        
        # Upsert DiscoveryCandidate
        upsert_candidates(workspace.id, "RECOMMENDED", recommended[:100])
        upsert_candidates(workspace.id, "TRENDING", trending[:100])
```

---

### E) API Endpoints

#### 1. Découverte

```http
GET /api/discovery?mode=recommended|trending&filters=...&page=...
```

**Response:**
```json
{
  "items": [
    {
      "artistId": "uuid",
      "name": "Tiakola",
      "score": 78,
      "timing": "3_6M",
      "recommendation": "BOOK",
      "driversTop2": [
        {"label": "Croissance virale", "impact": "+15"},
        {"label": "Playlist boost", "impact": "+10"}
      ],
      "dataQuality": "HIGH",
      "lastUpdated": "2026-01-26T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 87
  }
}
```

#### 2. Recherche / Lancer analyse

```http
POST /api/discovery/search
Content-Type: application/json

{
  "inputType": "VIBERATE_URL",
  "inputValue": "https://www.viberate.com/artist/tiakola"
}
```

**Response (success):**
```json
{
  "status": "JOB_CREATED",
  "jobId": "uuid",
  "artistId": "uuid"
}
```

**Response (ambiguïté):**
```json
{
  "status": "NEED_SELECTION",
  "candidates": [
    {"name": "Tiakola", "viberateUrl": "...", "spotifyId": "..."},
    {"name": "Tiakola (DJ)", "viberateUrl": "...", "spotifyId": null}
  ]
}
```

#### 3. Confirmation sélection

```http
POST /api/discovery/search/confirm
Content-Type: application/json

{
  "jobId": "uuid",
  "chosenCandidate": {
    "viberateUrl": "https://www.viberate.com/artist/tiakola"
  }
}
```

#### 4. Suivi jobs

```http
GET /api/discovery/jobs?status=queued,running&limit=10

GET /api/discovery/jobs/:id
```

**Response job:**
```json
{
  "id": "uuid",
  "inputValue": "Tiakola",
  "artistId": "uuid",
  "status": "RUNNING",
  "currentStep": "VIBERATE",
  "progressPct": 35,
  "createdAt": "2026-01-26T10:00:00Z"
}
```

#### 5. Comparaison

```http
POST /api/comparison/lists
{"name": "Shortlist Festival 2026"}

GET /api/comparison/lists

POST /api/comparison/lists/:id/items
{"artistId": "uuid"}

DELETE /api/comparison/lists/:id/items/:artistId

GET /api/comparison/lists/:id
# Returns items + computed metrics snapshot
```

#### 6. Rafraîchir (explicit)

```http
POST /api/artists/:id/refresh
```

**Response:**
```json
{
  "jobId": "uuid",
  "status": "JOB_CREATED",
  "startStep": "VIBERATE"
}
```

---

### F) Security / RBAC

| Règle | Description |
|-------|-------------|
| Scope workspace | Tout est filtré par `workspace_id` |
| Jobs visibilité | Membres du workspace voient leurs jobs |
| Logs détaillés | `logsRef` visible Admin only |
| Rate limit user | Max 10 jobs/min par user |

---

## 🖥️ Frontend — Architecture

### A) Page Découverte (`/discovery`)

#### Layout Desktop

```
┌──────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                    │
│ ┌────────────────────────────────┐  ┌──────────┐  ┌───────────┬────────┐│
│ │ 🔍 URL Viberate/Spotify/Nom... │  │ Analyser │  │ Recommandé│Tendances││
│ └────────────────────────────────┘  └──────────┘  └───────────┴────────┘│
│                                                                          │
│ FILTRES (chips)                                                          │
│ ┌────────┐ ┌─────────┐ ┌──────────────┐ ┌──────────┐ ┌─────────────────┐│
│ │ Timing │ │ Score   │ │ Taille aud.  │ │ Qualité  │ │ Mis à jour     ││
│ └────────┘ └─────────┘ └──────────────┘ └──────────┘ └─────────────────┘│
├──────────────────────────────────────────────────┬───────────────────────┤
│ BODY (Grid 2-3 colonnes)                         │ QUEUE                 │
│                                                  │                       │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ Analyses en cours     │
│ │ ArtistCard  │ │ ArtistCard  │ │ ArtistCard  │ │                       │
│ │ ─────────── │ │ ─────────── │ │ ─────────── │ │ ┌─────────────────┐  │
│ │ Tiakola     │ │ Ninho       │ │ Aya Nakam   │ │ │ ⏳ Tiakola      │  │
│ │ Score: 78   │ │ Score: 65   │ │ Score: 82   │ │ │ VIBERATE 35%   │  │
│ │ 📅 3-6 mois │ │ 📅 6-12 mois│ │ 📅 Imminent │ │ └─────────────────┘  │
│ │ ⚡ BOOK     │ │ 👁 WATCHLIST│ │ 🔥 BOOK     │ │                       │
│ │ [Ouvrir]    │ │ [Ouvrir]    │ │ [Ouvrir]    │ │ ┌─────────────────┐  │
│ │ [+ Comparer]│ │ [+ Comparer]│ │ [+ Comparer]│ │ │ ✅ Aya Nakam    │  │
│ └─────────────┘ └─────────────┘ └─────────────┘ │ │ DONE           │  │
│                                                  │ └─────────────────┘  │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │                       │
│ │ ArtistCard  │ │ ArtistCard  │ │ ArtistCard  │ │                       │
│ └─────────────┘ └─────────────┘ └─────────────┘ │                       │
│                                                  │                       │
│ [Charger plus...]                               │                       │
└──────────────────────────────────────────────────┴───────────────────────┘
```

#### Composant ArtistCard

```tsx
interface ArtistCardProps {
  artistId: string;
  name: string;
  score: number;
  timing: TimingBucket;
  recommendation: "BOOK" | "WATCHLIST" | "IGNORE";
  driversTop2: Driver[];
  dataQuality: "HIGH" | "MEDIUM" | "LOW";
  lastUpdated: string;
  platforms: {
    spotify?: boolean;
    instagram?: boolean;
    tiktok?: boolean;
    youtube?: boolean;
  };
}

// Actions
// - "Ouvrir" → navigate /artists/:id
// - "Ajouter à comparaison" → modal select shortlist
// - "Suivre" / "Épingler" (optionnel)
```

#### Composant JobQueuePanel

```tsx
interface Job {
  id: string;
  inputValue: string;
  artistId?: string;
  status: "QUEUED" | "RUNNING" | "PARTIAL" | "FAILED" | "DONE";
  currentStep: "MATCH" | "VIBERATE" | "SPOTIFY" | "COMPUTE";
  progressPct: number;
  errorMessage?: string;
}

// Actions par status:
// - DONE → "Ouvrir fiche"
// - FAILED → "Réessayer" + message erreur simplifié
// - RUNNING → progress bar animée
```

#### Règles UI Performance

| Règle | Implémentation |
|-------|----------------|
| Feed uniquement | Charge `/api/discovery` (feed) + `/api/discovery/jobs` (queue) |
| Pas de requête lourde scroll | Debounce filtres 300ms, pagination lazy |
| Navigation légère | "Ouvrir" = `router.push`, pas de prefetch lourd |

---

### B) Page Comparaison (`/comparison`)

#### Vue 1: Comparaison Rapide (2-4 colonnes)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                    │
│ ┌────────────────────────┐  ┌────────────────┐                           │
│ │ Shortlist: Festival 26 │  │ + Créer liste  │                           │
│ └────────────────────────┘  └────────────────┘                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ COMPARAISON (max 4 artistes)                                             │
│                                                                          │
│              │   Tiakola      │   Aya Nakamura  │   Ninho         │     │
│ ─────────────┼────────────────┼─────────────────┼─────────────────┼─────│
│ DÉCISION     │                │                 │                 │     │
│   Score      │      78        │       82        │       65        │     │
│   Timing     │    3-6 mois    │    Imminent     │    6-12 mois    │     │
│   Reco       │   ⚡ BOOK      │    🔥 BOOK      │   👁 WATCHLIST  │     │
│ ─────────────┼────────────────┼─────────────────┼─────────────────┼─────│
│ DRIVERS      │                │                 │                 │     │
│   #1         │ Croissance +15 │ Viral +20       │ Playlist +8     │     │
│   #2         │ Playlist +10   │ Collab +12      │ Social +5       │     │
│   #3         │ Social +8      │ Label +10       │ -               │     │
│ ─────────────┼────────────────┼─────────────────┼─────────────────┼─────│
│ RISQUES      │                │                 │                 │     │
│              │ -              │ Volatilité -5   │ Données -10     │     │
│ ─────────────┼────────────────┼─────────────────┼─────────────────┼─────│
│ ÉVOLUTION    │                │                 │                 │     │
│   (6 mois)   │  ▁▂▃▅▆█        │  ▂▃▄▅▇█         │  ▃▃▄▄▅▅         │     │
│ ─────────────┼────────────────┼─────────────────┼─────────────────┼─────│
│ SIGNAUX      │                │                 │                 │     │
│              │ 🔥 Viral       │ 🎵 Playlist     │ -               │     │
│              │ 🎵 Playlist    │ 🤝 Collab       │                 │     │
│ ─────────────┼────────────────┼─────────────────┼─────────────────┼─────│
│ CACHET       │                │                 │                 │     │
│   Estimé     │  4K - 6K €     │  8K - 12K €     │  3K - 5K €      │     │
│ ─────────────┼────────────────┼─────────────────┼─────────────────┼─────│
│ QUALITÉ      │                │                 │                 │     │
│   Données    │  ✅ HIGH       │  ✅ HIGH        │  ⚠️ MEDIUM      │     │
│   Màj        │  Il y a 2h     │  Il y a 1h      │  Il y a 6h      │     │
│ ─────────────┼────────────────┼─────────────────┼─────────────────┼─────│
│ ACTIONS      │                │                 │                 │     │
│              │ [Ouvrir]       │ [Ouvrir]        │ [Ouvrir]        │     │
│              │ [Retirer]      │ [Retirer]       │ [Retirer]       │     │
│              │ [🔄 Refresh]   │ [🔄 Refresh]    │ [🔄 Refresh]    │     │
└──────────────┴────────────────┴─────────────────┴─────────────────┴─────┘
```

> **Limite stricte**: Max 4 artistes simultanés (UX lisibilité)

#### Vue 2: Gestion Shortlists

```
┌──────────────────────────────────────────────────────────────┐
│ MES SHORTLISTS                                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 📋 Festival Été 2026                                   │  │
│ │    4 artistes • Màj il y a 2h                          │  │
│ │    [Ouvrir] [Renommer] [Supprimer]                     │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 📋 Prospects Q2                                        │  │
│ │    2 artistes • Màj il y a 1j                          │  │
│ │    [Ouvrir] [Renommer] [Supprimer]                     │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ [+ Créer nouvelle shortlist]                                 │
└──────────────────────────────────────────────────────────────┘
```

---

### C) State Management

#### React Query Configuration

```tsx
// Discovery feed
useQuery({
  queryKey: ['discovery', mode, filters, page],
  queryFn: () => fetchDiscoveryFeed(mode, filters, page),
  staleTime: 60_000,      // 60s
  cacheTime: 180_000,     // 3min
});

// Jobs queue
useQuery({
  queryKey: ['discovery', 'jobs', workspaceId],
  queryFn: () => fetchJobs({ status: ['queued', 'running', 'partial', 'failed'] }),
  refetchInterval: (data) => {
    // 2-5s si jobs RUNNING, sinon 30s
    const hasRunning = data?.some(j => j.status === 'RUNNING');
    return hasRunning ? 3_000 : 30_000;
  },
});

// Comparison list
useQuery({
  queryKey: ['comparison', 'list', listId],
  queryFn: () => fetchComparisonList(listId),
  staleTime: 60_000,
  refetchOnWindowFocus: true,
});
```

#### Optimistic Updates

```tsx
// Add to shortlist
useMutation({
  mutationFn: addToShortlist,
  onMutate: async ({ listId, artistId }) => {
    await queryClient.cancelQueries(['comparison', 'list', listId]);
    const previous = queryClient.getQueryData(['comparison', 'list', listId]);
    
    queryClient.setQueryData(['comparison', 'list', listId], (old) => ({
      ...old,
      items: [...old.items, { artistId, addedAt: new Date() }]
    }));
    
    return { previous };
  },
  onError: (err, vars, context) => {
    queryClient.setQueryData(['comparison', 'list', vars.listId], context.previous);
    toast.error("Erreur lors de l'ajout");
  },
});
```

#### Error Handling (Toasts)

| État | Message |
|------|---------|
| Job créé | "Analyse lancée pour {name}" |
| Job en cours | Progress bar silencieuse |
| Job terminé | "Analyse terminée - {name} ajouté" |
| Job partiel | "⚠️ Analyse partielle - Données incomplètes" |
| Job échoué | "❌ Échec analyse - {raison simple}" |

---

### D) Empty States

#### Découverte - Aucun candidat

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                    🔍                                        │
│                                                              │
│          Aucun artiste à afficher                           │
│                                                              │
│   Ajoutez votre première analyse pour découvrir             │
│   des artistes à fort potentiel.                            │
│                                                              │
│   ┌─────────────────────────────────────────┐               │
│   │  Analyser une URL Viberate ou Spotify   │               │
│   └─────────────────────────────────────────┘               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### Découverte - Filtres trop restrictifs

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│          Aucun résultat avec ces filtres                    │
│                                                              │
│   Essayez d'élargir vos critères de recherche.             │
│                                                              │
│   [Réinitialiser les filtres]                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### Comparaison - Shortlist vide

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                    📋                                        │
│                                                              │
│          Cette shortlist est vide                           │
│                                                              │
│   Ajoutez 2 à 4 artistes depuis Découverte                  │
│   ou la page Artistes pour les comparer.                    │
│                                                              │
│   [Aller à Découverte]                                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 📝 Conventions Produit

| Règle | Implémentation |
|-------|----------------|
| Pas de "probabilité" | Utiliser "Indice breakout" si affiché |
| Toujours afficher qualité | Badge `dataQuality` + "Dernière mise à jour" obligatoires |
| Messages erreur simples | Pas de stack traces, messages user-friendly |

#### Messages d'erreur Job

| Code | Message affiché | Action |
|------|-----------------|--------|
| `SOURCE_UNAVAILABLE` | "Source indisponible" | Réessayer |
| `RATE_LIMITED` | "Limite atteinte, réessayez plus tard" | Attendre |
| `PARSER_CHANGED` | "Page modifiée" | Contacter support |
| `NOT_FOUND` | "Artiste non trouvé" | Vérifier URL |
| `TIMEOUT` | "Délai dépassé" | Réessayer |

---

## ✅ Critères d'Acceptation

### Tests obligatoires

| # | Test | Validation |
|---|------|------------|
| 1 | **Découverte passive** | Ouvrir `/discovery` ne déclenche aucun scraping (vérifier logs réseau) |
| 2 | **Performance feed** | `/api/discovery` p95 < 300-500ms sur cache chaud |
| 3 | **Job tracking** | Recherche URL Viberate → job visible avec progression MATCH→VIBERATE→SPOTIFY→COMPUTE |
| 4 | **Persistance** | Computed metrics réutilisés (reload page = pas de re-scrape) |
| 5 | **Comparaison read-only** | Affiche 2-4 artistes avec uniquement des GET computed (aucun scrape) |
| 6 | **Refresh explicite** | Bouton "Rafraîchir" crée job async, met à jour computed à la fin |
| 7 | **Data quality update** | `dataQuality` se met à jour selon succès/partiel/échec sources |
| 8 | **Anti-doublons** | Artiste existant → proposer "ouvrir existant" ou "nouveau snapshot", jamais doublon silencieux |

---

## 📦 Livrables

### Backend

- [ ] Migrations DB (7 entités)
- [ ] Worker pipeline 4 étapes + rate limit + retry
- [ ] Cache Redis (TTL configurables)
- [ ] Job planifié `generate_discovery_candidates`
- [ ] Endpoints API (8 routes)
- [ ] RBAC workspace scope
- [ ] Tests unitaires pipeline
- [ ] Tests intégration API

### Frontend

- [ ] Page `/discovery` : feed + filtres + search + job queue
- [ ] Page `/comparison` : shortlists + comparaison 2-4 colonnes
- [ ] Composants: `ArtistCard`, `JobQueuePanel`, `ComparisonTable`
- [ ] États: loading / empty / error
- [ ] Toasts notifications
- [ ] Tests E2E Playwright

---

## ⚠️ Règle d'or

> **Toute donnée affichée sur Découverte/Comparaison provient UNIQUEMENT de `ArtistComputedMetrics` / `DiscoveryCandidate`.**
>
> **Toute extraction web scraping se fait UNIQUEMENT via job async, JAMAIS dans une requête UI.**

---

*Spec générée le 26 janvier 2026 - V3.0*
