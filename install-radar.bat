@echo off
chcp 65001 >nul
title Radar - Installation Automatique
color 0B

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                                                              ║
echo  ║   ██████╗  █████╗ ██████╗  █████╗ ██████╗                   ║
echo  ║   ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗                  ║
echo  ║   ██████╔╝███████║██║  ██║███████║██████╔╝                  ║
echo  ║   ██╔══██╗██╔══██║██║  ██║██╔══██║██╔══██╗                  ║
echo  ║   ██║  ██║██║  ██║██████╔╝██║  ██║██║  ██║                  ║
echo  ║   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝                  ║
echo  ║                                                              ║
echo  ║            Installation Plug ^& Play                         ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

:: ============================================
:: VERIFICATION DES PREREQUIS
:: ============================================

echo [1/6] Verification des prerequis...
echo.

:: Check Docker
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERREUR] Docker n'est pas installe ou n'est pas dans le PATH.
    echo           Installez Docker Desktop: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)
echo  [OK] Docker detecte

:: Check Docker Compose
docker-compose --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    docker compose version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo  [ERREUR] Docker Compose n'est pas installe.
        echo.
        pause
        exit /b 1
    )
)
echo  [OK] Docker Compose detecte

:: Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERREUR] Docker n'est pas demarre. Veuillez lancer Docker Desktop.
    echo.
    pause
    exit /b 1
)
echo  [OK] Docker est en cours d'execution
echo.

:: ============================================
:: CONFIGURATION DU FICHIER .ENV
:: ============================================

echo [2/6] Configuration de l'environnement...
echo.

if not exist .env (
    echo  Creation du fichier .env...
    (
        echo # ============================================
        echo # RADAR - Configuration
        echo # ============================================
        echo.
        echo # Database
        echo POSTGRES_USER=radar_user
        echo POSTGRES_PASSWORD=radar_password_2024
        echo POSTGRES_DB=radar_db
        echo DATABASE_URL=postgresql://radar_user:radar_password_2024@postgres:5432/radar_db
        echo.
        echo # Security
        echo SECRET_KEY=radar-secret-key-change-in-production-2024
        echo.
        echo # Backend
        echo BACKEND_URL=http://localhost:8000
        echo.
        echo # Frontend
        echo NEXT_PUBLIC_API_URL=http://localhost:8000
        echo.
        echo # Redis
        echo REDIS_URL=redis://redis:6379/0
        echo.
        echo # OpenAI ^(optionnel - pour les fonctions IA^)
        echo OPENAI_API_KEY=
        echo.
        echo # Spotify ^(optionnel^)
        echo SPOTIFY_CLIENT_ID=
        echo SPOTIFY_CLIENT_SECRET=
    ) > .env
    echo  [OK] Fichier .env cree avec les valeurs par defaut
) else (
    echo  [OK] Fichier .env existant detecte
)
echo.

:: ============================================
:: ARRET DES ANCIENS CONTAINERS
:: ============================================

echo [3/6] Nettoyage des anciens containers...
echo.

docker-compose down --remove-orphans >nul 2>&1
echo  [OK] Anciens containers arretes
echo.

:: ============================================
:: CONSTRUCTION DES IMAGES
:: ============================================

echo [4/6] Construction des images Docker...
echo      (Cette etape peut prendre quelques minutes)
echo.

docker-compose build --no-cache
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [ERREUR] La construction des images a echoue.
    echo.
    pause
    exit /b 1
)
echo.
echo  [OK] Images construites avec succes
echo.

:: ============================================
:: DEMARRAGE DES SERVICES
:: ============================================

echo [5/6] Demarrage des services...
echo.

docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [ERREUR] Le demarrage des services a echoue.
    echo.
    pause
    exit /b 1
)

:: Wait for services to be healthy
echo  Attente du demarrage des services...
timeout /t 15 /nobreak >nul

echo  [OK] Services demarres
echo.

:: ============================================
:: MIGRATION DE LA BASE DE DONNEES
:: ============================================

echo [6/6] Migration de la base de donnees...
echo.

docker-compose exec -T backend alembic upgrade head >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [INFO] Migration en cours de retry...
    timeout /t 5 /nobreak >nul
    docker-compose exec -T backend alembic upgrade head
)
echo  [OK] Base de donnees prete
echo.

:: ============================================
:: TERMINE !
:: ============================================

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                                                              ║
echo  ║   ✓ INSTALLATION TERMINEE AVEC SUCCES !                     ║
echo  ║                                                              ║
echo  ╠══════════════════════════════════════════════════════════════╣
echo  ║                                                              ║
echo  ║   Frontend:  http://localhost:3000                          ║
echo  ║   Backend:   http://localhost:8000                          ║
echo  ║   API Docs:  http://localhost:8000/docs                     ║
echo  ║                                                              ║
echo  ╠══════════════════════════════════════════════════════════════╣
echo  ║                                                              ║
echo  ║   Compte par defaut:                                        ║
echo  ║   Email:    admin@radar.com                                 ║
echo  ║   Password: admin123                                        ║
echo  ║                                                              ║
echo  ╠══════════════════════════════════════════════════════════════╣
echo  ║                                                              ║
echo  ║   Commandes utiles:                                         ║
echo  ║   - Arreter:    docker-compose down                         ║
echo  ║   - Demarrer:   docker-compose up -d                        ║
echo  ║   - Logs:       docker-compose logs -f                      ║
echo  ║                                                              ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

:: Open browser
echo Ouverture du navigateur dans 3 secondes...
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
pause
