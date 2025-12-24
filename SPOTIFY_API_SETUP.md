# Configuration de l'API Spotify

Ce guide explique comment obtenir les credentials Spotify pour que l'application puisse récupérer les données d'artistes (auditeurs mensuels, genres, popularité, etc.).

## 🎯 Pourquoi Spotify API ?

L'API Spotify officielle fournit des données **précises et à jour** sur les artistes :
- ✅ Nombre d'**auditeurs mensuels exact**
- ✅ **Genres musicaux corrects** (pas de devinettes)
- ✅ Score de **popularité** (0-100)
- ✅ Nombre de **followers**
- ✅ Albums, singles, top tracks

**Avant :** Web scraping → données incorrectes (Spotify=0, Genre=Unknown)  
**Après :** API officielle → données fiables pour tous les artistes

## 📝 Étapes pour obtenir les credentials

### 1. Créer un compte développeur Spotify

1. Aller sur https://developer.spotify.com/dashboard
2. Se connecter avec votre compte Spotify (ou en créer un)
3. Accepter les conditions d'utilisation

### 2. Créer une application

1. Cliquer sur **"Create app"**
2. Remplir le formulaire :
   - **App name:** `Opportunities Radar` (ou autre nom)
   - **App description:** `Application pour analyser les artistes et opportunités musicales`
   - **Website:** `http://localhost:3000` (ou votre domaine)
   - **Redirect URI:** `http://localhost:8000/callback` (non utilisé pour notre cas)
   - **API:** Cocher `Web API`
3. Accepter les conditions
4. Cliquer sur **"Save"**

### 3. Récupérer les credentials

1. Sur la page de votre app, cliquer sur **"Settings"**
2. Vous verrez :
   - **Client ID:** `1234567890abcdef1234567890abcdef`
   - **Client Secret:** Cliquer sur "View client secret" pour l'afficher

⚠️ **IMPORTANT:** Ne partagez JAMAIS votre Client Secret publiquement

### 4. Configurer l'application

#### Option A : Fichier `.env` (Recommandé)

1. Créer un fichier `.env` à la racine du projet (si pas déjà existant)
2. Copier le contenu de `.env.example`
3. Ajouter vos credentials Spotify :

```bash
# Spotify API
SPOTIFY_CLIENT_ID=votre_client_id_ici
SPOTIFY_CLIENT_SECRET=votre_client_secret_ici
```

#### Option B : Variables d'environnement Docker

Éditer `docker-compose.yml` et ajouter dans les sections `backend`, `worker`, et `scheduler` :

```yaml
environment:
  - SPOTIFY_CLIENT_ID=votre_client_id_ici
  - SPOTIFY_CLIENT_SECRET=votre_client_secret_ici
```

### 5. Redémarrer les conteneurs Docker

```bash
docker-compose restart backend worker
```

## ✅ Vérification

Pour vérifier que l'API Spotify fonctionne :

1. Aller sur le dashboard : http://localhost:3000/dashboard
2. Cliquer sur **"Analyser"** pour un artiste (ex: Nayra, Kerchak)
3. Vérifier dans les logs Docker :

```bash
docker logs radar_backend | grep Spotify
```

Vous devriez voir :
```
✅ Spotify API client initialized successfully
✅ Spotify API: Nayra - 250,000 followers, genre: RAP, popularity: 65
```

## 📊 Données récupérées

L'API Spotify fournit pour chaque artiste :

| Donnée | Type | Exemple |
|--------|------|---------|
| Nom | string | "Nayra" |
| Followers | int | 250,000 |
| Popularité | int (0-100) | 65 |
| Genres | array | ["french hip hop", "rap francais"] |
| URL Spotify | string | https://open.spotify.com/artist/... |
| Image | string (URL) | https://i.scdn.co/image/... |

## 🔄 Limites et quotas

### Spotify Web API - Mode Client Credentials

- **✅ Gratuit** pour un usage raisonnable
- **Rate limit:** ~1000 requêtes / seconde (largement suffisant)
- **Pas de limite** sur le nombre d'artistes
- **Pas d'authentification utilisateur** requise (mode machine-to-machine)

### Ce qui est inclus :

- ✅ Recherche d'artistes
- ✅ Informations d'artistes (followers, genres, popularité)
- ✅ Albums et singles
- ✅ Top tracks
- ❌ Playlists personnelles (nécessite OAuth utilisateur)
- ❌ Lecture de musique (pas nécessaire pour nous)

## 🛠️ Dépannage

### "Spotify API not configured"

Vérifier que les variables d'environnement sont bien définies :

```bash
docker exec radar_backend printenv | grep SPOTIFY
```

Devrait afficher :
```
SPOTIFY_CLIENT_ID=1234567890abcdef...
SPOTIFY_CLIENT_SECRET=abcdef1234567890...
```

### "Spotify API not available"

1. Vérifier que `spotipy` est installé :
```bash
docker exec radar_backend pip list | grep spotipy
```

2. Si absent, rebuild les images :
```bash
docker-compose build backend worker
docker-compose up -d
```

### "No Spotify results for: [artiste]"

L'artiste n'existe pas sur Spotify ou le nom est mal orthographié. Essayer :
- Le nom exact de l'artiste sur Spotify
- Enlever les accents
- Essayer en anglais si artiste international

## 🔗 Ressources

- **Documentation Spotify API:** https://developer.spotify.com/documentation/web-api
- **Dashboard développeur:** https://developer.spotify.com/dashboard
- **Bibliothèque spotipy (Python):** https://spotipy.readthedocs.io
- **Exemples de code:** https://github.com/spotipy-dev/spotipy/tree/master/examples

## 🚀 Prochaines étapes (optionnel)

Après Spotify, on peut ajouter d'autres APIs :

1. **YouTube Data API v3** (gratuit, 10,000 requêtes/jour)
   - Nombre d'abonnés YouTube
   - Total de vues
   - Vidéos récentes

2. **Instagram Graph API** (limité, nécessite compte business)
   - Followers Instagram
   - Engagement rate

3. **TikTok API** (via RapidAPI, quotas limités)
   - Followers TikTok
   - Vues totales

Pour l'instant, **Spotify seul est largement suffisant** pour obtenir des estimations fiables ! 🎉
