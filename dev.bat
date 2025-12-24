@echo off
chcp 65001 >nul
title Opportunities Radar - Mode Développement

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║        🎯 OPPORTUNITIES RADAR - DÉVELOPPEMENT             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:menu
echo ┌────────────────────────────────────────────────────────────┐
echo │               MODE DÉVELOPPEMENT                           │
echo ├────────────────────────────────────────────────────────────┤
echo │  1. Démarrer Backend (FastAPI dev)                         │
echo │  2. Démarrer Frontend (Next.js dev)                        │
echo │  3. Démarrer services Docker (DB + Redis seulement)        │
echo │  4. Installer dépendances Backend                          │
echo │  5. Installer dépendances Frontend                         │
echo │  6. Créer migration Alembic                                │
echo │  7. Appliquer migrations                                   │
echo │  8. Lancer Celery Worker                                   │
echo │  9. Lancer Celery Beat                                     │
echo │  0. Quitter                                                │
echo └────────────────────────────────────────────────────────────┘
echo.

set /p choice="Votre choix: "

if "%choice%"=="1" goto backend
if "%choice%"=="2" goto frontend
if "%choice%"=="3" goto services
if "%choice%"=="4" goto install_backend
if "%choice%"=="5" goto install_frontend
if "%choice%"=="6" goto create_migration
if "%choice%"=="7" goto apply_migration
if "%choice%"=="8" goto celery_worker
if "%choice%"=="9" goto celery_beat
if "%choice%"=="0" goto end

echo ❌ Choix invalide
goto menu

:backend
echo.
echo 🐍 Démarrage du backend FastAPI...
cd backend
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  Environnement virtuel non trouvé. Création...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
)
start cmd /k "cd /d %cd% && .venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
cd ..
echo ✅ Backend démarré sur http://localhost:8000
echo.
pause
goto menu

:frontend
echo.
echo ⚛️  Démarrage du frontend Next.js...
cd frontend
start cmd /k "cd /d %cd% && npm run dev"
cd ..
echo ✅ Frontend démarré sur http://localhost:3000
echo.
pause
goto menu

:services
echo.
echo 🐳 Démarrage PostgreSQL et Redis...
docker-compose up -d postgres redis
echo ✅ Services de base démarrés
echo    PostgreSQL: localhost:5432
echo    Redis: localhost:6379
echo.
pause
goto menu

:install_backend
echo.
echo 📦 Installation des dépendances Backend...
cd backend
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..
echo ✅ Dépendances Backend installées
echo.
pause
goto menu

:install_frontend
echo.
echo 📦 Installation des dépendances Frontend...
cd frontend
call npm install
cd ..
echo ✅ Dépendances Frontend installées
echo.
pause
goto menu

:create_migration
echo.
set /p msg="Message de la migration: "
cd backend
call .venv\Scripts\activate.bat
alembic revision --autogenerate -m "%msg%"
cd ..
echo ✅ Migration créée
echo.
pause
goto menu

:apply_migration
echo.
echo 📦 Application des migrations...
cd backend
call .venv\Scripts\activate.bat
alembic upgrade head
cd ..
echo ✅ Migrations appliquées
echo.
pause
goto menu

:celery_worker
echo.
echo 🔄 Démarrage Celery Worker...
cd backend
start cmd /k "cd /d %cd% && .venv\Scripts\activate.bat && celery -A app.workers.celery_app worker -l info -P solo"
cd ..
echo ✅ Celery Worker démarré
echo.
pause
goto menu

:celery_beat
echo.
echo ⏰ Démarrage Celery Beat...
cd backend
start cmd /k "cd /d %cd% && .venv\Scripts\activate.bat && celery -A app.workers.celery_app beat -l info"
cd ..
echo ✅ Celery Beat démarré
echo.
pause
goto menu

:end
echo.
echo 👋 Au revoir !
exit /b 0
