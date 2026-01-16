#!/bin/bash

# Script d'initialisation Let's Encrypt pour radarapp.fr
# Exécuter une seule fois sur le serveur

DOMAIN="radarapp.fr"
EMAIL="aymanamir@outlook.fr"  # Ton email pour les notifications

echo "=== Initialisation SSL pour $DOMAIN ==="

# Créer les dossiers nécessaires
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Étape 1: Démarrer nginx en mode HTTP uniquement
echo "Étape 1: Configuration nginx en mode HTTP..."
cp ./docker/nginx/nginx.init.conf ./docker/nginx/nginx.active.conf

# Mettre à jour docker-compose pour utiliser la config init
docker compose down nginx 2>/dev/null

# Démarrer nginx avec config HTTP
docker compose up -d nginx

echo "Attente du démarrage de nginx..."
sleep 10

# Vérifier que nginx répond
echo "Test de nginx..."
curl -s http://localhost/.well-known/acme-challenge/test 2>/dev/null || true

# Étape 2: Obtenir le certificat Let's Encrypt
echo ""
echo "Étape 2: Obtention du certificat Let's Encrypt..."
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d $DOMAIN \
    -d www.$DOMAIN

# Vérifier si le certificat a été obtenu
if [ -f "./certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo ""
    echo "✅ Certificat obtenu avec succès!"
    echo ""
    echo "Étape 3: Activation de HTTPS..."
    
    # Copier la config SSL
    cp ./docker/nginx/nginx.ssl.conf ./docker/nginx/nginx.active.conf
    
    # Redémarrer nginx avec SSL
    docker compose restart nginx
    
    # Démarrer certbot pour le renouvellement auto
    docker compose up -d certbot
    
    echo ""
    echo "=== ✅ SSL configuré avec succès ! ==="
    echo "Accède à https://$DOMAIN"
else
    echo ""
    echo "❌ Erreur: Le certificat n'a pas pu être obtenu"
    echo "Vérifie que le domaine $DOMAIN pointe vers ce serveur"
    echo "Le site reste accessible en HTTP: http://$DOMAIN"
fi
