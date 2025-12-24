@echo off
chcp 65001 >nul
title Opportunities Radar - Démarrage

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║           🎯 OPPORTUNITIES RADAR - SETUP                   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: Vérifier si Docker est installé
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker n'est pas installé ou n'est pas dans le PATH
    echo    Téléchargez Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

:: Vérifier si Docker est en cours d'exécution
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker n'est pas en cours d'exécution
    echo    Démarrez Docker Desktop et réessayez
    pause
    exit /b 1
)

echo ✅ Docker est disponible
echo.

:: Créer le fichier .env s'il n'existe pas
if not exist .env (
    echo 📝 Création du fichier .env...
    copy .env.example .env >nul
    echo ✅ Fichier .env créé (pensez à le configurer)
) else (
    echo ✅ Fichier .env existant
)
echo.

:: Menu principal
:menu
echo ┌────────────────────────────────────────────────────────────┐
echo │                    MENU PRINCIPAL                          │
echo ├────────────────────────────────────────────────────────────┤
echo │  1. Démarrer tous les services                             │
echo │  2. Initialiser la base de données (première fois)         │
echo │  3. Arrêter tous les services                              │
echo │  4. Voir les logs                                          │
echo │  5. Reconstruire les images                                │
echo │  6. Nettoyer tout (volumes inclus)                         │
echo │  7. Ouvrir l'application dans le navigateur                │
echo │  8. Status des services                                    │
echo │  0. Quitter                                                │
echo └────────────────────────────────────────────────────────────┘
echo.

set /p choice="Votre choix: "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto init
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto rebuild
if "%choice%"=="6" goto clean
if "%choice%"=="7" goto open
if "%choice%"=="8" goto status
if "%choice%"=="0" goto end

echo ❌ Choix invalide
goto menu

:start
echo.
echo 🚀 Démarrage des services...
docker-compose up -d
echo.
echo ✅ Services démarrés !
echo.
echo    Frontend:  http://localhost:3000
echo    API:       http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
pause
goto menu

:init
echo.
echo 📦 Initialisation de la base de données...
echo.
echo    Attente du démarrage de PostgreSQL (10s)...
timeout /t 10 /nobreak >nul

echo    Exécution des migrations Alembic...
docker-compose exec -T backend python -m alembic upgrade head

echo    Chargement des données de test...
docker-compose exec -T backend python -m app.db.seed

echo.
echo ✅ Base de données initialisée !
echo.
echo    Comptes de test:
echo    ┌─────────────────────────────┬─────────────┬─────────┐
echo    │ Email                       │ Mot de passe│ Rôle    │
echo    ├─────────────────────────────┼─────────────┼─────────┤
echo    │ admin@agency.fr             │ admin123    │ Admin   │
echo    │ marie.dupont@agency.fr      │ bizdev123   │ BizDev  │
echo    │ pierre.martin@agency.fr     │ pm123       │ PM      │
echo    └─────────────────────────────┴─────────────┴─────────┘
echo.
pause
goto menu

:stop
echo.
echo 🛑 Arrêt des services...
docker-compose down
echo ✅ Services arrêtés
echo.
pause
goto menu

:logs
echo.
echo 📋 Affichage des logs (Ctrl+C pour quitter)...
echo.
docker-compose logs -f
goto menu

:rebuild
echo.
echo 🔨 Reconstruction des images Docker...
docker-compose build --no-cache
echo ✅ Images reconstruites
echo.
pause
goto menu

:clean
echo.
echo ⚠️  ATTENTION: Cette action supprimera toutes les données !
set /p confirm="Êtes-vous sûr ? (oui/non): "
if /i "%confirm%"=="oui" (
    echo 🧹 Nettoyage en cours...
    docker-compose down -v --remove-orphans
    docker system prune -f
    echo ✅ Nettoyage terminé
) else (
    echo Annulé
)
echo.
pause
goto menu

:open
echo.
echo 🌐 Ouverture du navigateur...
start http://localhost:3000
goto menu

:status
echo.
echo 📊 Status des services:
echo.
docker-compose ps
echo.
pause
goto menu

:end
echo.
echo 👋 Au revoir !
exit /b 0
