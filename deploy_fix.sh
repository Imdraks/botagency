#!/bin/bash
cd /opt/radar

echo "=== Pulling latest changes ==="
git pull

echo "=== Rebuilding backend ==="
docker compose -f docker-compose.prod.yml build backend

echo "=== Restarting backend ==="
docker compose -f docker-compose.prod.yml up -d backend

echo "=== Waiting for backend to start ==="
sleep 5

echo "=== Checking backend logs ==="
docker compose -f docker-compose.prod.yml logs backend --tail=20

echo "=== Done! ==="
