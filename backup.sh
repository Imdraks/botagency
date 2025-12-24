#!/bin/bash
# ===========================================
# Script de backup pour radarapp.fr
# ===========================================

BACKUP_DIR="/home/deploy/backups"
APP_DIR="/home/deploy/botagency"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Créer le dossier de backup
mkdir -p $BACKUP_DIR

cd $APP_DIR

echo "🗄️ Backup de la base de données..."

# Backup PostgreSQL
docker compose -f docker-compose.prod.yml exec -T postgres pg_dump \
    -U radar_prod \
    -d opportunities_radar \
    --format=custom \
    > "$BACKUP_DIR/db_backup_$DATE.dump"

# Compression
gzip "$BACKUP_DIR/db_backup_$DATE.dump"

echo "✅ Backup créé: $BACKUP_DIR/db_backup_$DATE.dump.gz"

# Backup du fichier .env
cp $APP_DIR/.env "$BACKUP_DIR/env_backup_$DATE"

# Supprimer les backups de plus de X jours
find $BACKUP_DIR -name "db_backup_*.dump.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "env_backup_*" -mtime +$RETENTION_DAYS -delete

echo "🧹 Anciens backups nettoyés (rétention: $RETENTION_DAYS jours)"

# Afficher l'espace utilisé
echo ""
echo "📊 Espace utilisé par les backups:"
du -sh $BACKUP_DIR

# Lister les backups disponibles
echo ""
echo "📁 Backups disponibles:"
ls -lh $BACKUP_DIR
