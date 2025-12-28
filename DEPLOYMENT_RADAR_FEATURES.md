# 🚀 Guide de Déploiement - Radar Features v2

Ce guide vous accompagne pour déployer les 6 nouvelles fonctionnalités Radar sur votre VPS OVH.

## 📋 Nouvelles Fonctionnalités

| # | Fonctionnalité | Description |
|---|----------------|-------------|
| 1 | **Daily Picks (Shortlist)** | Sélection quotidienne des meilleures opportunités par l'IA |
| 2 | **Clusters (Dédup)** | Détection intelligente des doublons |
| 3 | **Profiles (Fit Score)** | Scoring personnalisé par profil utilisateur |
| 4 | **Deadline Guard** | Alertes J-7/J-3/J-1 sur les échéances |
| 5 | **Source Health** | Monitoring de la qualité des sources |
| 6 | **Contact Finder** | Recherche automatique de contacts |

---

## 🔧 Prérequis

- Accès SSH au VPS
- Docker et Docker Compose installés
- Git installé
- Base de données PostgreSQL accessible

---

## 📝 Étapes de Déploiement

### 1. Connexion au VPS

```bash
ssh user@votre-vps.ovh.net
cd /path/to/botagency
```

### 2. Sauvegarde de la base de données (RECOMMANDÉ)

```bash
# Créer un dump de sauvegarde
docker exec postgres-container pg_dump -U radarapp radarapp > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 3. Pull des dernières modifications

```bash
git pull origin main
```

### 4. Build des nouvelles images Docker

```bash
# Build backend avec les nouvelles dépendances
docker-compose -f docker-compose.prod.yml build backend

# Build frontend avec les nouvelles pages
docker-compose -f docker-compose.prod.yml build frontend
```

### 5. Appliquer la migration Alembic

```bash
# Exécuter la migration pour créer les nouvelles tables
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Vérifier que la migration 012_radar_features est appliquée
docker-compose -f docker-compose.prod.yml exec backend alembic current
```

### 6. Redémarrer les services

```bash
# Redémarrage complet avec les nouveaux containers
docker-compose -f docker-compose.prod.yml up -d

# Vérifier le statut
docker-compose -f docker-compose.prod.yml ps
```

### 7. Vérifier les logs

```bash
# Logs backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Logs Celery worker
docker-compose -f docker-compose.prod.yml logs -f celery-worker

# Logs Celery beat (jobs planifiés)
docker-compose -f docker-compose.prod.yml logs -f celery-beat
```

---

## 🔍 Vérification Post-Déploiement

### Tester les nouveaux endpoints API

```bash
# Health check backend
curl https://radarapp.fr/api/v1/health

# Tester l'API Profiles
curl -X GET https://radarapp.fr/api/v1/profiles \
  -H "Authorization: Bearer YOUR_TOKEN"

# Tester l'API Source Health
curl -X GET https://radarapp.fr/api/v1/sources/health/overview \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Vérifier les nouvelles pages Frontend

1. **Daily Picks**: https://radarapp.fr/shortlist
2. **Profils**: https://radarapp.fr/profiles
3. **Deadlines**: https://radarapp.fr/deadlines
4. **Source Health**: https://radarapp.fr/source-health

### Vérifier les Jobs Celery Beat

```bash
# Voir les jobs planifiés
docker-compose -f docker-compose.prod.yml exec celery-worker celery -A app.workers.celery_app inspect scheduled
```

---

## ⏰ Schedule des Jobs Celery

| Job | Heure | Description |
|-----|-------|-------------|
| `source-health-rollup` | 01:00 | Calcul de la santé des sources |
| `auto-build-dossiers` | 02:00 | Construction auto des dossiers |
| `cluster-rebuild-nightly` | 03:00 | Reconstruction des clusters |
| `deadline-guard-check` | 07:00 | Vérification des deadlines |
| `daily-shortlist-generation` | 08:00 | Génération des shortlists |
| `auto-radar-harvest` | */15 min | Récolte automatique |

---

## 🐛 Troubleshooting

### La migration échoue

```bash
# Voir le statut actuel des migrations
docker-compose -f docker-compose.prod.yml exec backend alembic history

# Rollback si nécessaire
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

### Les jobs Celery ne s'exécutent pas

```bash
# Redémarrer Celery Beat
docker-compose -f docker-compose.prod.yml restart celery-beat

# Vérifier la configuration Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli PING
```

### Erreurs Frontend

```bash
# Rebuild complet du frontend
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

---

## 📊 Nouvelles Tables de Base de Données

La migration `012_radar_features` crée les tables suivantes:

| Table | Description |
|-------|-------------|
| `profiles` | Profils de matching utilisateur |
| `opportunity_profile_scores` | Scores par opportunité/profil |
| `daily_shortlists` | Shortlists quotidiennes |
| `opportunity_clusters` | Groupes de doublons |
| `opportunity_cluster_members` | Membres des clusters |
| `deadline_alerts` | Alertes de deadline |
| `source_health` | Métriques de santé des sources |
| `contact_finder_results` | Résultats de recherche de contacts |

---

## ✅ Checklist Finale

- [ ] Backup de la base de données effectué
- [ ] Migration Alembic appliquée
- [ ] Backend redémarré sans erreur
- [ ] Frontend accessible
- [ ] Celery Beat en cours d'exécution
- [ ] Nouvelles pages accessibles
- [ ] Jobs planifiés visibles
- [ ] Logs sans erreur critique

---

## 🔄 Rollback en cas de problème

```bash
# 1. Rollback de la migration
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade 011_refonte_collectes

# 2. Restaurer la sauvegarde si nécessaire
docker exec -i postgres-container psql -U radarapp radarapp < backup_YYYYMMDD_HHMMSS.sql

# 3. Checkout de la version précédente
git checkout HEAD~1

# 4. Rebuild et redémarrer
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📞 Support

En cas de problème:
1. Consulter les logs: `docker-compose logs -f`
2. Vérifier les erreurs dans la base de données
3. Contacter l'équipe de développement

---

**Version**: 2.0.0  
**Date**: $(date +%Y-%m-%d)  
**Auteur**: Équipe Radar
