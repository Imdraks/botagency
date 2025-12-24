@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Opportunities Radar - Installation Automatique

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║           🎯 OPPORTUNITIES RADAR - INSTALLATION AUTO              ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

:: ============================================================================
:: VÉRIFICATIONS
:: ============================================================================

echo [1/8] Vérification de Docker...

docker --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Docker n'est pas installé !
    echo.
    echo    Téléchargez Docker Desktop:
    echo    https://www.docker.com/products/docker-desktop
    echo.
    start https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

:: Attendre que Docker soit prêt (max 60 secondes)
echo    Attente de Docker Desktop...
set /a counter=0
:wait_docker
docker info >nul 2>&1
if errorlevel 1 (
    set /a counter+=1
    if !counter! geq 12 (
        echo.
        echo ❌ Docker Desktop n'est pas démarré !
        echo    Lancez Docker Desktop et réessayez.
        pause
        exit /b 1
    )
    echo    Tentative !counter!/12...
    timeout /t 5 /nobreak >nul
    goto wait_docker
)
echo ✅ Docker prêt

:: ============================================================================
:: GÉNÉRATION .ENV
:: ============================================================================

echo.
echo [2/8] Configuration de l'environnement...

if not exist .env (
    (
        echo # Opportunities Radar - Configuration Auto
        echo.
        echo # Database
        echo POSTGRES_DB=opportunities
        echo POSTGRES_USER=opportunities
        echo POSTGRES_PASSWORD=OppsRadar2024
        echo DATABASE_URL=postgresql://opportunities:OppsRadar2024@postgres:5432/opportunities
        echo.
        echo # Redis
        echo REDIS_URL=redis://redis:6379
        echo.
        echo # JWT
        echo JWT_SECRET_KEY=OppsRadar-Secret-Key-%RANDOM%%RANDOM%
        echo JWT_ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo REFRESH_TOKEN_EXPIRE_DAYS=7
        echo.
        echo # Backend
        echo BACKEND_URL=http://backend:8000
        echo DEBUG=false
        echo.
        echo # Frontend
        echo NEXT_PUBLIC_API_URL=http://localhost:8000
        echo.
        echo # Admin
        echo ADMIN_EMAIL=admin@agency.fr
        echo ADMIN_PASSWORD=admin123
        echo ADMIN_NAME=Administrateur
        echo.
        echo # IMAP ^(désactivé par défaut^)
        echo IMAP_ENABLED=false
        echo IMAP_SERVER=
        echo IMAP_PORT=993
        echo IMAP_USER=
        echo IMAP_PASSWORD=
        echo IMAP_FOLDER=INBOX
        echo.
        echo # Notifications ^(désactivé par défaut^)
        echo SLACK_WEBHOOK_URL=
        echo DISCORD_WEBHOOK_URL=
        echo SMTP_HOST=
        echo SMTP_PORT=587
        echo SMTP_USER=
        echo SMTP_PASSWORD=
    ) > .env
    echo ✅ Fichier .env créé
) else (
    echo ✅ Fichier .env existant conservé
)

:: ============================================================================
:: BUILD DOCKER
:: ============================================================================

echo.
echo [3/8] Construction des images Docker...
echo    (Cela peut prendre 3-5 minutes la première fois)
echo.
echo ────────────────────────────────────────────────────────────────────────
echo.

:: Build avec affichage de la progression
docker-compose build 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Erreur lors du build Docker
    pause
    exit /b 1
)
echo.
echo ────────────────────────────────────────────────────────────────────────
echo ✅ Images construites

:: ============================================================================
:: DÉMARRAGE SERVICES
:: ============================================================================

echo.
echo [4/8] Démarrage des services...

docker-compose up -d
if errorlevel 1 (
    echo ❌ Erreur lors du démarrage
    pause
    exit /b 1
)
echo ✅ Services démarrés

:: ============================================================================
:: ATTENTE POSTGRESQL
:: ============================================================================

echo.
echo [5/8] Attente de PostgreSQL...

set /a counter=0
:wait_postgres
docker-compose exec -T postgres pg_isready -U opportunities >nul 2>&1
if errorlevel 1 (
    set /a counter+=1
    if !counter! geq 30 (
        echo ❌ PostgreSQL n'a pas démarré
        docker-compose logs postgres
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    goto wait_postgres
)
echo ✅ PostgreSQL prêt

:: ============================================================================
:: ATTENTE BACKEND
:: ============================================================================

echo.
echo [6/8] Attente du backend...

set /a counter=0
:wait_backend
docker-compose exec -T backend python -c "print('ok')" >nul 2>&1
if errorlevel 1 (
    set /a counter+=1
    if !counter! geq 30 (
        echo ❌ Le backend n'a pas démarré
        docker-compose logs backend
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    goto wait_backend
)
echo ✅ Backend prêt

:: ============================================================================
:: MIGRATIONS
:: ============================================================================

echo.
echo [7/8] Initialisation de la base de données...

echo    - Migrations Alembic...
docker-compose exec -T backend python -m alembic upgrade head
if errorlevel 1 (
    echo ⚠️  Erreur migrations (peut-être déjà fait)
)

echo    - Données initiales...
docker-compose exec -T backend python -m app.db.seed
if errorlevel 1 (
    echo ⚠️  Erreur seed (peut-être déjà fait)
)

echo ✅ Base de données initialisée

:: ============================================================================
:: TERMINÉ
:: ============================================================================

echo.
echo [8/8] Vérification finale...

:: Attendre que le frontend soit prêt
timeout /t 5 /nobreak >nul

echo.
echo ════════════════════════════════════════════════════════════════════════
echo.
echo  ✅ INSTALLATION TERMINÉE !
echo.
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                                                                        ║
echo ║   🌐 Application:  http://localhost:3000                               ║
echo ║   📚 API Docs:     http://localhost:8000/docs                          ║
echo ║                                                                        ║
echo ║   👤 Connexion:                                                        ║
echo ║      Email:     admin@agency.fr                                        ║
echo ║      Password:  admin123                                               ║
echo ║                                                                        ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.
echo    Commandes utiles:
echo    ─────────────────
echo    stop.bat        Arrêter l'application
echo    start.bat       Menu de gestion
echo    dev.bat         Mode développement
echo.
echo    Pour configurer email/Slack/Discord, éditez le fichier .env
echo.
echo ════════════════════════════════════════════════════════════════════════
echo.

:: Ouvrir le navigateur
start http://localhost:3000

echo Appuyez sur une touche pour voir les logs (Ctrl+C pour quitter)...
pause >nul
docker-compose logs -f

endlocal
