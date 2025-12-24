@echo off
chcp 65001 >nul
title Opportunities Radar - Quick Start

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║        🎯 OPPORTUNITIES RADAR - QUICK START               ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: Vérifier Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker n'est pas en cours d'exécution
    echo    Démarrez Docker Desktop et réessayez
    pause
    exit /b 1
)

:: Créer .env si nécessaire
if not exist .env (
    echo 📝 Création du fichier .env...
    copy .env.example .env >nul
)

:: Démarrer les services
echo 🚀 Démarrage de tous les services...
docker-compose up -d

:: Attendre que les services soient prêts
echo ⏳ Attente du démarrage des services (15s)...
timeout /t 15 /nobreak >nul

:: Vérifier si c'est la première exécution
docker-compose exec -T postgres psql -U opportunities -d opportunities -c "SELECT 1 FROM users LIMIT 1;" >nul 2>&1
if errorlevel 1 (
    echo 📦 Première exécution détectée - Initialisation de la base...
    docker-compose exec -T backend python -m alembic upgrade head
    docker-compose exec -T backend python -m app.db.seed
    echo ✅ Base de données initialisée
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    ✅ PRÊT !                               ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║  Frontend:  http://localhost:3000                          ║
echo ║  API:       http://localhost:8000                          ║
echo ║  API Docs:  http://localhost:8000/docs                     ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║  Connexion: admin@agency.fr / admin123                     ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: Ouvrir le navigateur
start http://localhost:3000

echo Appuyez sur une touche pour voir les logs (Ctrl+C pour quitter)...
pause >nul
docker-compose logs -f
