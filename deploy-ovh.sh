#!/bin/bash
# ===========================================
# Script de déploiement OVH pour radarapp.fr
# ===========================================

set -e

DOMAIN="radarapp.fr"
APP_DIR="/home/deploy/botagency"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Déploiement de Opportunities Radar sur ${DOMAIN}${NC}"
echo "=================================================="

# 1. Mise à jour système
echo -e "${YELLOW}📦 Mise à jour du système...${NC}"
sudo apt update && sudo apt upgrade -y

# 2. Installation des dépendances
echo -e "${YELLOW}🔧 Installation de Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# Installation Docker Compose plugin
sudo apt install -y docker-compose-plugin git curl

# 3. Configuration du firewall
echo -e "${YELLOW}🔒 Configuration du firewall...${NC}"
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 4. Configuration du swap (recommandé pour VPS 4GB)
echo -e "${YELLOW}💾 Configuration du swap...${NC}"
if [ ! -f /swapfile ]; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# 5. Cloner ou mettre à jour le projet
echo -e "${YELLOW}📥 Récupération du projet...${NC}"
if [ -d "$APP_DIR" ]; then
    cd $APP_DIR
    git pull
else
    cd /home/deploy
    git clone https://github.com/VOTRE_REPO/botagency.git
    cd $APP_DIR
fi

# 6. Créer le fichier .env si inexistant
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚙️ Création du fichier .env...${NC}"
    
    # Générer des clés aléatoires
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
    
    cat > .env << EOF
# ===========================================
# Configuration Production - radarapp.fr
# ===========================================

# Application
APP_NAME=Radar
APP_ENV=production
DEBUG=false
SECRET_KEY=${SECRET_KEY}
FRONTEND_URL=https://${DOMAIN}
BACKEND_URL=https://${DOMAIN}

# Database
POSTGRES_USER=radar_prod
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=opportunities_radar
DATABASE_URL=postgresql://radar_prod:${DB_PASSWORD}@postgres:5432/opportunities_radar

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# JWT Auth
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# IMAP Email (à configurer)
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=
IMAP_PASSWORD=
IMAP_FOLDER=NEWSLETTERS
IMAP_USE_SSL=true

# SMTP Notifications (à configurer)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=

# Webhooks (optionnel)
DISCORD_WEBHOOK_URL=
SLACK_WEBHOOK_URL=

# Spotify API (optionnel)
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=

# OpenAI API (optionnel)
OPENAI_API_KEY=

# Google OAuth (optionnel)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
EOF

    echo -e "${GREEN}✅ Fichier .env créé avec des clés sécurisées${NC}"
    echo -e "${YELLOW}⚠️  Pensez à configurer les services optionnels dans .env${NC}"
fi

# 7. Lancer les containers
echo -e "${YELLOW}🐳 Lancement des containers Docker...${NC}"
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
docker compose -f docker-compose.prod.yml up -d --build

# 8. Attendre que PostgreSQL soit prêt
echo -e "${YELLOW}⏳ Attente de PostgreSQL...${NC}"
sleep 10

# 9. Initialiser la base de données
echo -e "${YELLOW}🗄️ Initialisation de la base de données...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
docker compose -f docker-compose.prod.yml exec -T backend python -m app.db.seed || true

# 10. Installer Certbot pour HTTPS
echo -e "${YELLOW}🔐 Configuration HTTPS avec Let's Encrypt...${NC}"
sudo apt install -y certbot python3-certbot-nginx nginx

# Créer config Nginx temporaire pour Certbot
sudo tee /etc/nginx/sites-available/${DOMAIN} > /dev/null << EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};
    
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/${DOMAIN} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Obtenir le certificat SSL
echo -e "${YELLOW}📜 Obtention du certificat SSL...${NC}"
sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN} --non-interactive --agree-tos --email admin@${DOMAIN} || {
    echo -e "${YELLOW}⚠️  Certbot a échoué. Assurez-vous que le DNS pointe vers ce serveur.${NC}"
    echo -e "${YELLOW}   Relancez: sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}${NC}"
}

# 11. Configurer le renouvellement automatique SSL
echo "0 3 * * * root certbot renew --quiet" | sudo tee /etc/cron.d/certbot-renew

# 12. Afficher le statut
echo ""
echo -e "${GREEN}=================================================="
echo "✅ Déploiement terminé !"
echo "==================================================${NC}"
echo ""
echo "📊 Statut des containers:"
docker compose -f docker-compose.prod.yml ps
echo ""
echo -e "${GREEN}🌐 Votre application est disponible sur:${NC}"
echo "   → https://${DOMAIN}"
echo "   → https://${DOMAIN}/docs (API Documentation)"
echo ""
echo -e "${YELLOW}📝 Prochaines étapes:${NC}"
echo "   1. Vérifiez que le DNS de ${DOMAIN} pointe vers ce serveur"
echo "   2. Configurez les services dans .env (IMAP, SMTP, etc.)"
echo "   3. Configurez les backups automatiques"
echo ""
