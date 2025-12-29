# 🚀 Guide de Déploiement VPS - Radar

## Prérequis VPS

- Ubuntu 22.04 LTS (recommandé)
- 2 vCPU minimum / 4 Go RAM
- 40 Go SSD
- Docker & Docker Compose installés
- Domaine configuré (ex: radar.tondomaine.com)

---

## 🔧 Installation initiale (première fois)

```bash
# 1. Connexion SSH
ssh root@ton-serveur-ip

# 2. Créer l'utilisateur deploy
adduser deploy
usermod -aG docker deploy
usermod -aG sudo deploy

# 3. Installer les dépendances
apt update && apt upgrade -y
apt install -y docker.io docker-compose-v2 nginx certbot python3-certbot-nginx git

# 4. Activer Docker
systemctl enable docker
systemctl start docker

# 5. Cloner le projet
su - deploy
cd /opt
sudo mkdir radar && sudo chown deploy:deploy radar
git clone https://github.com/Imdraks/radar.git /opt/radar
cd /opt/radar

# 6. Configuration
cp .env.example .env
nano .env  # Configurer les variables (voir section ci-dessous)

# 7. Rendre les scripts exécutables
chmod +x deploy.sh monitor.sh

# 8. Premier déploiement
./deploy.sh --full
```

---

## ⚡ Déploiement rapide (mises à jour)

```bash
# Connexion au VPS
ssh deploy@ton-serveur-ip

# Déploiement
cd /opt/radar
./deploy.sh --quick
```

**Options du script deploy.sh :**
| Commande | Description |
|----------|-------------|
| `./deploy.sh --quick` | Pull git + restart containers |
| `./deploy.sh --full` | Full rebuild (images + migrations) |
| `./deploy.sh --rollback` | Retour au commit précédent |
| `./deploy.sh --status` | État des services |
| `./deploy.sh --logs` | Logs en temps réel |
| `./deploy.sh --backup` | Backup manuel de la DB |

---

## 🔐 Variables d'environnement (.env)

```env
# Database
POSTGRES_SERVER=postgres
POSTGRES_USER=radar_user
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD
POSTGRES_DB=radar

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Backend
SECRET_KEY=GENERATE_WITH_openssl_rand_-hex_32
BACKEND_URL=https://radar.tondomaine.com
ENVIRONMENT=production

# Frontend
NEXT_PUBLIC_API_URL=https://radar.tondomaine.com/api

# OAuth (optionnel)
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
SPOTIFY_CLIENT_ID=xxx
SPOTIFY_CLIENT_SECRET=xxx

# OpenAI
OPENAI_API_KEY=sk-xxx
```

---

## 🌐 Configuration Nginx + SSL

```bash
# 1. Copier la config Nginx
sudo cp docker/nginx/nginx.conf /etc/nginx/sites-available/radar

# 2. Ou créer manuellement
sudo nano /etc/nginx/sites-available/radar
```

**Contenu nginx :**
```nginx
server {
    listen 80;
    server_name radar.tondomaine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name radar.tondomaine.com;

    ssl_certificate /etc/letsencrypt/live/radar.tondomaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/radar.tondomaine.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# 3. Activer le site
sudo ln -s /etc/nginx/sites-available/radar /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# 4. SSL avec Let's Encrypt
sudo certbot --nginx -d radar.tondomaine.com

# 5. Tester et recharger
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📊 Monitoring

```bash
# Dashboard temps réel
./monitor.sh

# Logs d'un service
docker compose logs -f backend

# Status Docker
docker compose ps

# Métriques système
htop
```

---

## 🔄 Commandes utiles

```bash
# Redémarrer un service
docker compose restart backend

# Voir les logs
docker compose logs -f --tail=100 backend

# Accéder à un container
docker compose exec backend bash

# Base de données
docker compose exec postgres psql -U radar_user -d radar

# Migrations manuelles
docker compose exec backend alembic upgrade head

# Backup manuel
docker compose exec postgres pg_dump -U radar_user radar > backup_$(date +%Y%m%d).sql

# Restaurer un backup
cat backup_20250129.sql | docker compose exec -T postgres psql -U radar_user radar
```

---

## 🚨 Troubleshooting

### Container ne démarre pas
```bash
docker compose logs <service_name>
docker compose up <service_name>  # Mode attaché pour debug
```

### Problème de permissions
```bash
sudo chown -R deploy:deploy /opt/radar
chmod -R 755 /opt/radar
```

### Base de données corrompue
```bash
./deploy.sh --rollback  # Revenir au commit précédent
docker compose down -v  # ⚠️ Supprime les volumes
./deploy.sh --full
```

### Certificat SSL expiré
```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## 🔒 Sécurité recommandée

```bash
# Firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban

# SSH keys only
nano /etc/ssh/sshd_config
# PasswordAuthentication no
sudo systemctl restart sshd
```

---

## 📅 Cron jobs automatiques

```bash
crontab -e
```

```cron
# Backup quotidien à 3h du matin
0 3 * * * /opt/radar/deploy.sh --backup

# Renouvellement SSL (2x par jour)
0 0,12 * * * certbot renew --quiet

# Nettoyage Docker hebdomadaire
0 4 * * 0 docker system prune -af --volumes
```

---

## 🎯 Checklist déploiement

- [ ] VPS provisionné avec IP fixe
- [ ] DNS configuré (A record vers IP)
- [ ] SSH configuré (clés, pas de password)
- [ ] Docker installé
- [ ] Projet cloné dans /opt/radar
- [ ] .env configuré
- [ ] `./deploy.sh --full` réussi
- [ ] Nginx configuré
- [ ] SSL activé (Let's Encrypt)
- [ ] Firewall activé (ufw)
- [ ] Fail2ban installé
- [ ] Crons configurés (backup, SSL)
- [ ] Health check OK: `curl https://radar.tondomaine.com/health`

---

**🎉 Ton application est maintenant en production !**

Créé le 29/12/2024 - Commit 8de901b
