# 🚀 Optimisations de Performance - Radar

## Vue d'ensemble

Ce document résume les optimisations de performance et de sécurité appliquées à l'application Radar.

---

## ✅ Optimisations Frontend (Next.js)

### 1. Configuration Next.js (`next.config.js`)
- **Compression GZip** activée côté serveur
- **Security Headers** ajoutés :
  - `X-XSS-Protection`
  - `X-Frame-Options` (DENY)
  - `X-Content-Type-Options` (nosniff)
  - `Referrer-Policy` (strict-origin-when-cross-origin)
- **Cache agressif** pour assets statiques (1 an)
- **Optimisation des imports** pour lucide-react, radix-ui, date-fns
- **Optimisation des images** : AVIF/WebP + cache 30 jours
- **Removal du header X-Powered-By**

### 2. React Query (`providers.tsx`)
- `staleTime` augmenté à 5 minutes (vs 60s avant)
- `gcTime` (garbage collection) : 30 minutes
- `refetchOnReconnect` désactivé pour éviter les appels inutiles
- `retry` limité à 1 tentative
- **DevTools lazy-loaded** uniquement en développement

### 3. API Client (`api.ts`)
- **Timeout** de 30 secondes sur toutes les requêtes
- **Accept-Encoding** explicite pour compression

### 4. Performance Utilities (`performance.ts`) - NOUVEAU
- `useDebounce` - Pour les champs de recherche
- `useIntersectionObserver` - Lazy loading du contenu
- `useVirtualList` - Listes virtuelles pour grands datasets
- `throttle` - Pour les événements de scroll/resize
- `createLazyComponent` - Composants lazy-loaded avec spinner

---

## ✅ Optimisations Backend (FastAPI)

### 1. Middlewares (`main.py`)
- **GZipMiddleware** : Compression automatique des réponses > 500 bytes
- **TimingMiddleware** : Log des requêtes lentes (> 1s) + header `X-Process-Time`
- **CORS optimisé** : Cache preflight de 10 minutes

### 2. Base de données (`session.py`)
- **Pool de connexions optimisé** :
  - `pool_size` : 20 connexions (vs 5 par défaut)
  - `max_overflow` : 30 connexions supplémentaires
  - `pool_timeout` : 30 secondes
  - `pool_recycle` : 30 minutes (évite les connexions périmées)
- **Query timeout** : 30 secondes par requête (PostgreSQL)
- **expire_on_commit=False** : Réduit les requêtes de rechargement

### 3. Cache Redis (`cache.py`) - NOUVEAU
- Pool de connexions Redis (50 max)
- Fonctions utilitaires :
  - `cache_get(key)` - Récupère du cache
  - `cache_set(key, value, ttl)` - Stocke en cache
  - `cache_result(prefix, ttl)` - Décorateur de cache
  - `invalidate_cache(prefix)` - Invalidation par préfixe

### 4. Endpoints cachés

| Endpoint | TTL | Description |
|----------|-----|-------------|
| `/dashboard/stats` | 60s | Statistiques du dashboard |
| `/dashboard/top-opportunities` | 120s | Top opportunités |
| `/sources/health/overview` | 300s | Santé des sources |

### 5. Index de base de données (`014_performance_indexes.py`)
- `ix_opportunities_status_score` - Filtre status + tri par score
- `ix_opportunities_deadline_at` - Tri par deadline
- `ix_opportunities_created_at` - Tri par date de création
- `ix_opportunities_category` - Filtre par catégorie
- `ix_opportunities_status_deadline` - Combiné status + deadline
- `ix_source_health_source_date` - Historique santé sources
- `ix_activity_logs_created_at` - Logs par date
- `ix_activity_logs_user_action` - Logs par utilisateur/action
- `ix_profiles_user_active` - Profils actifs par utilisateur
- `ix_shortlists_profile_date` - Shortlists par profil/date

---

## 📊 Gains attendus

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| TTFB Dashboard | ~2s | ~200ms | **~90%** |
| Taille réponse API | 100% | ~30% | **~70%** (GZip) |
| Requêtes DB/session | 100% | ~50% | **~50%** (cache) |
| Connexions DB | Illimitées | Poolées | **Stable** |

---

## 🔒 Améliorations Sécurité

1. **Headers de sécurité** standards
2. **Timeout** sur toutes les requêtes (évite les DOS)
3. **Pool de connexions limité** (évite les ressources épuisées)
4. **X-Powered-By** supprimé (masque la stack)
5. **Referrer-Policy** strict

---

## 📋 Prochaines étapes recommandées

1. [ ] Ajouter le cache aux endpoints `/opportunities` (TTL 30s)
2. [ ] Implémenter la pagination cursor-based pour grandes listes
3. [ ] Ajouter CDN pour les assets statiques
4. [ ] Configurer HTTP/2 sur le reverse proxy
5. [ ] Ajouter des métriques APM (Sentry, DataDog)
6. [ ] Implémenter le lazy-loading sur les composants lourds

---

## 🛠️ Déploiement

```bash
# Localement
docker-compose down
docker-compose build --no-cache backend frontend
docker-compose up -d

# Appliquer les index DB
docker exec radar_backend alembic upgrade head
```

---

*Dernière mise à jour : $(date)*
