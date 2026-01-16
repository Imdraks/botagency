#!/bin/bash

# Script d'initialisation Let's Encrypt pour radarapp.fr
# Exécuter une seule fois sur le serveur

DOMAIN="radarapp.fr"
EMAIL="contact@radarapp.fr"  # Change avec ton email

echo "=== Initialisation SSL pour $DOMAIN ==="

# Créer les dossiers nécessaires
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Arrêter nginx temporairement si en cours
docker compose stop nginx 2>/dev/null

# Télécharger les paramètres SSL recommandés
if [ ! -f "./certbot/conf/options-ssl-nginx.conf" ]; then
    echo "Téléchargement des paramètres SSL..."
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > ./certbot/conf/options-ssl-nginx.conf
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > ./certbot/conf/ssl-dhparams.pem
fi

# Créer un certificat temporaire pour démarrer nginx
echo "Création d'un certificat temporaire..."
mkdir -p ./certbot/conf/live/$DOMAIN
docker run --rm -v $(pwd)/certbot/conf:/etc/letsencrypt alpine sh -c "
    mkdir -p /etc/letsencrypt/live/$DOMAIN
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
        -out /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
        -subj '/CN=localhost'
"

# Démarrer nginx avec le certificat temporaire
echo "Démarrage de nginx..."
docker compose up -d nginx

# Attendre que nginx soit prêt
sleep 5

# Supprimer le certificat temporaire
rm -rf ./certbot/conf/live/$DOMAIN

# Obtenir le vrai certificat Let's Encrypt
echo "Obtention du certificat Let's Encrypt..."
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Redémarrer nginx avec le vrai certificat
echo "Redémarrage de nginx avec SSL..."
docker compose restart nginx

echo ""
echo "=== SSL configuré avec succès ! ==="
echo "Accède à https://$DOMAIN"
