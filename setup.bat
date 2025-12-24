@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Opportunities Radar - Configuration Initiale

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║           🎯 OPPORTUNITIES RADAR - CONFIGURATION INITIALE         ║
echo ║                                                                    ║
echo ║   Ce script va configurer votre environnement de A à Z            ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

:: ============================================================================
:: VÉRIFICATIONS PRÉALABLES
:: ============================================================================

echo 📋 Vérification des prérequis...
echo.

:: Vérifier Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker n'est pas installé
    echo.
    echo    👉 Téléchargez Docker Desktop:
    echo       https://www.docker.com/products/docker-desktop
    echo.
    echo    Après installation, relancez ce script.
    pause
    exit /b 1
)
echo ✅ Docker installé

:: Vérifier si Docker tourne
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Desktop n'est pas démarré
    echo.
    echo    👉 Lancez Docker Desktop et attendez qu'il soit prêt
    echo       (icône baleine stable dans la barre des tâches)
    echo.
    pause
    exit /b 1
)
echo ✅ Docker en cours d'exécution

:: Vérifier Git (optionnel)
git --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Git non installé (optionnel mais recommandé)
) else (
    echo ✅ Git installé
)

echo.
echo ════════════════════════════════════════════════════════════════════
echo.

:: ============================================================================
:: CONFIGURATION DE LA BASE DE DONNÉES
:: ============================================================================

echo 🗄️  CONFIGURATION BASE DE DONNÉES
echo ─────────────────────────────────
echo.

set "DB_NAME=opportunities"
set "DB_USER=opportunities"

echo Nom de la base de données [opportunities]:
set /p "input_db_name="
if not "!input_db_name!"=="" set "DB_NAME=!input_db_name!"

echo Utilisateur PostgreSQL [opportunities]:
set /p "input_db_user="
if not "!input_db_user!"=="" set "DB_USER=!input_db_user!"

echo Mot de passe PostgreSQL (min 8 caractères):
set /p "DB_PASSWORD="
if "!DB_PASSWORD!"=="" (
    echo ⚠️  Génération d'un mot de passe aléatoire...
    set "DB_PASSWORD=OppsRadar2024!%RANDOM%"
)

echo.
echo ✅ Base de données configurée
echo.

:: ============================================================================
:: CONFIGURATION JWT (SÉCURITÉ)
:: ============================================================================

echo 🔐 CONFIGURATION SÉCURITÉ JWT
echo ─────────────────────────────
echo.

echo Clé secrète JWT (laissez vide pour génération automatique):
set /p "JWT_SECRET="
if "!JWT_SECRET!"=="" (
    :: Générer une clé aléatoire
    set "JWT_SECRET=OppsRadar-Secret-%RANDOM%%RANDOM%%RANDOM%-%DATE:~-4%%TIME:~0,2%%TIME:~3,2%"
    echo ✅ Clé JWT générée automatiquement
) else (
    echo ✅ Clé JWT personnalisée définie
)

set "JWT_ALGO=HS256"
set "ACCESS_TOKEN_EXPIRE=30"
set "REFRESH_TOKEN_EXPIRE=7"

echo.

:: ============================================================================
:: CONFIGURATION EMAIL IMAP (GMAIL)
:: ============================================================================

echo 📧 CONFIGURATION EMAIL IMAP (pour ingestion emails)
echo ────────────────────────────────────────────────────
echo.
echo ⚠️  Pour Gmail, vous devez:
echo    1. Activer l'accès IMAP dans Gmail
echo    2. Créer un "Mot de passe d'application" (pas votre mdp Gmail!)
echo       → https://myaccount.google.com/apppasswords
echo.

set "IMAP_ENABLED=false"
echo Voulez-vous configurer l'ingestion email ? (oui/non) [non]:
set /p "input_imap="
if /i "!input_imap!"=="oui" (
    set "IMAP_ENABLED=true"
    
    echo.
    echo Serveur IMAP [imap.gmail.com]:
    set /p "IMAP_SERVER="
    if "!IMAP_SERVER!"=="" set "IMAP_SERVER=imap.gmail.com"
    
    echo Port IMAP [993]:
    set /p "IMAP_PORT="
    if "!IMAP_PORT!"=="" set "IMAP_PORT=993"
    
    echo Adresse email (ex: votre-agence@gmail.com):
    set /p "IMAP_USER="
    
    echo Mot de passe d'application Gmail (16 caractères sans espaces):
    set /p "IMAP_PASSWORD="
    
    echo Dossier à surveiller [INBOX]:
    set /p "IMAP_FOLDER="
    if "!IMAP_FOLDER!"=="" set "IMAP_FOLDER=INBOX"
    
    echo.
    echo ✅ Configuration email IMAP enregistrée
) else (
    set "IMAP_SERVER="
    set "IMAP_PORT=993"
    set "IMAP_USER="
    set "IMAP_PASSWORD="
    set "IMAP_FOLDER=INBOX"
    echo ⏭️  Configuration email ignorée (peut être ajoutée plus tard)
)

echo.

:: ============================================================================
:: CONFIGURATION NOTIFICATIONS
:: ============================================================================

echo 🔔 CONFIGURATION NOTIFICATIONS
echo ───────────────────────────────
echo.

:: Slack
set "SLACK_ENABLED=false"
echo Configurer les notifications Slack ? (oui/non) [non]:
set /p "input_slack="
if /i "!input_slack!"=="oui" (
    set "SLACK_ENABLED=true"
    echo.
    echo 💡 Pour obtenir un webhook Slack:
    echo    1. Allez sur https://api.slack.com/apps
    echo    2. Créez une app → Incoming Webhooks → Add New Webhook
    echo.
    echo URL du webhook Slack:
    set /p "SLACK_WEBHOOK_URL="
    echo ✅ Slack configuré
) else (
    set "SLACK_WEBHOOK_URL="
    echo ⏭️  Slack ignoré
)

echo.

:: Discord
set "DISCORD_ENABLED=false"
echo Configurer les notifications Discord ? (oui/non) [non]:
set /p "input_discord="
if /i "!input_discord!"=="oui" (
    set "DISCORD_ENABLED=true"
    echo.
    echo 💡 Pour obtenir un webhook Discord:
    echo    1. Paramètres du serveur → Intégrations → Webhooks
    echo    2. Créer un webhook → Copier l'URL
    echo.
    echo URL du webhook Discord:
    set /p "DISCORD_WEBHOOK_URL="
    echo ✅ Discord configuré
) else (
    set "DISCORD_WEBHOOK_URL="
    echo ⏭️  Discord ignoré
)

echo.

:: Email SMTP (pour envoyer des notifications)
set "SMTP_ENABLED=false"
echo Configurer les notifications par email (SMTP) ? (oui/non) [non]:
set /p "input_smtp="
if /i "!input_smtp!"=="oui" (
    set "SMTP_ENABLED=true"
    echo.
    echo Serveur SMTP [smtp.gmail.com]:
    set /p "SMTP_HOST="
    if "!SMTP_HOST!"=="" set "SMTP_HOST=smtp.gmail.com"
    
    echo Port SMTP [587]:
    set /p "SMTP_PORT="
    if "!SMTP_PORT!"=="" set "SMTP_PORT=587"
    
    echo Email expéditeur:
    set /p "SMTP_USER="
    
    echo Mot de passe SMTP (mot de passe d'application si Gmail):
    set /p "SMTP_PASSWORD="
    
    echo Email "From" affiché [!SMTP_USER!]:
    set /p "EMAIL_FROM="
    if "!EMAIL_FROM!"=="" set "EMAIL_FROM=!SMTP_USER!"
    
    echo ✅ SMTP configuré
) else (
    set "SMTP_HOST="
    set "SMTP_PORT=587"
    set "SMTP_USER="
    set "SMTP_PASSWORD="
    set "EMAIL_FROM="
    echo ⏭️  SMTP ignoré
)

echo.

:: ============================================================================
:: CONFIGURATION ADMIN
:: ============================================================================

echo 👤 CONFIGURATION COMPTE ADMIN
echo ──────────────────────────────
echo.

echo Email de l'admin [admin@agency.fr]:
set /p "ADMIN_EMAIL="
if "!ADMIN_EMAIL!"=="" set "ADMIN_EMAIL=admin@agency.fr"

echo Mot de passe admin (min 8 caractères) [admin123]:
set /p "ADMIN_PASSWORD="
if "!ADMIN_PASSWORD!"=="" set "ADMIN_PASSWORD=admin123"

echo Nom complet de l'admin [Administrateur]:
set /p "ADMIN_NAME="
if "!ADMIN_NAME!"=="" set "ADMIN_NAME=Administrateur"

echo.
echo ✅ Compte admin configuré
echo.

:: ============================================================================
:: CONFIGURATION PORTS
:: ============================================================================

echo 🌐 CONFIGURATION RÉSEAU
echo ────────────────────────
echo.

echo Port du frontend [3000]:
set /p "FRONTEND_PORT="
if "!FRONTEND_PORT!"=="" set "FRONTEND_PORT=3000"

echo Port de l'API backend [8000]:
set /p "BACKEND_PORT="
if "!BACKEND_PORT!"=="" set "BACKEND_PORT=8000"

echo Port PostgreSQL [5432]:
set /p "POSTGRES_PORT="
if "!POSTGRES_PORT!"=="" set "POSTGRES_PORT=5432"

echo.
echo ✅ Ports configurés
echo.

:: ============================================================================
:: GÉNÉRATION DU FICHIER .ENV
:: ============================================================================

echo ════════════════════════════════════════════════════════════════════
echo.
echo 📝 Génération du fichier .env...
echo.

(
echo # ============================================================================
echo # OPPORTUNITIES RADAR - Configuration
echo # Généré le %DATE% à %TIME%
echo # ============================================================================
echo.
echo # -----------------------------------------------------------------------------
echo # BASE DE DONNÉES POSTGRESQL
echo # -----------------------------------------------------------------------------
echo POSTGRES_DB=!DB_NAME!
echo POSTGRES_USER=!DB_USER!
echo POSTGRES_PASSWORD=!DB_PASSWORD!
echo POSTGRES_PORT=!POSTGRES_PORT!
echo DATABASE_URL=postgresql://!DB_USER!:!DB_PASSWORD!@postgres:5432/!DB_NAME!
echo.
echo # -----------------------------------------------------------------------------
echo # REDIS
echo # -----------------------------------------------------------------------------
echo REDIS_URL=redis://redis:6379
echo.
echo # -----------------------------------------------------------------------------
echo # SÉCURITÉ JWT
echo # -----------------------------------------------------------------------------
echo JWT_SECRET_KEY=!JWT_SECRET!
echo JWT_ALGORITHM=!JWT_ALGO!
echo ACCESS_TOKEN_EXPIRE_MINUTES=!ACCESS_TOKEN_EXPIRE!
echo REFRESH_TOKEN_EXPIRE_DAYS=!REFRESH_TOKEN_EXPIRE!
echo.
echo # -----------------------------------------------------------------------------
echo # BACKEND
echo # -----------------------------------------------------------------------------
echo BACKEND_URL=http://backend:8000
echo BACKEND_PORT=!BACKEND_PORT!
echo DEBUG=false
echo.
echo # -----------------------------------------------------------------------------
echo # FRONTEND
echo # -----------------------------------------------------------------------------
echo NEXT_PUBLIC_API_URL=http://localhost:!BACKEND_PORT!
echo FRONTEND_PORT=!FRONTEND_PORT!
echo.
echo # -----------------------------------------------------------------------------
echo # EMAIL IMAP (Ingestion)
echo # -----------------------------------------------------------------------------
echo IMAP_ENABLED=!IMAP_ENABLED!
echo IMAP_SERVER=!IMAP_SERVER!
echo IMAP_PORT=!IMAP_PORT!
echo IMAP_USER=!IMAP_USER!
echo IMAP_PASSWORD=!IMAP_PASSWORD!
echo IMAP_FOLDER=!IMAP_FOLDER!
echo IMAP_USE_SSL=true
echo.
echo # -----------------------------------------------------------------------------
echo # NOTIFICATIONS SLACK
echo # -----------------------------------------------------------------------------
echo SLACK_ENABLED=!SLACK_ENABLED!
echo SLACK_WEBHOOK_URL=!SLACK_WEBHOOK_URL!
echo.
echo # -----------------------------------------------------------------------------
echo # NOTIFICATIONS DISCORD
echo # -----------------------------------------------------------------------------
echo DISCORD_ENABLED=!DISCORD_ENABLED!
echo DISCORD_WEBHOOK_URL=!DISCORD_WEBHOOK_URL!
echo.
echo # -----------------------------------------------------------------------------
echo # NOTIFICATIONS EMAIL (SMTP)
echo # -----------------------------------------------------------------------------
echo SMTP_ENABLED=!SMTP_ENABLED!
echo SMTP_HOST=!SMTP_HOST!
echo SMTP_PORT=!SMTP_PORT!
echo SMTP_USER=!SMTP_USER!
echo SMTP_PASSWORD=!SMTP_PASSWORD!
echo NOTIFICATION_EMAIL_FROM=!EMAIL_FROM!
echo.
echo # -----------------------------------------------------------------------------
echo # COMPTE ADMIN INITIAL
echo # -----------------------------------------------------------------------------
echo ADMIN_EMAIL=!ADMIN_EMAIL!
echo ADMIN_PASSWORD=!ADMIN_PASSWORD!
echo ADMIN_NAME=!ADMIN_NAME!
) > .env

echo ✅ Fichier .env créé
echo.

:: ============================================================================
:: MISE À JOUR DU SEED AVEC LES INFOS ADMIN
:: ============================================================================

echo 📝 Configuration du compte admin dans le seed...

:: Créer un fichier Python temporaire pour mettre à jour les credentials admin
(
echo # Auto-generated admin config
echo ADMIN_EMAIL = "!ADMIN_EMAIL!"
echo ADMIN_PASSWORD = "!ADMIN_PASSWORD!"
echo ADMIN_NAME = "!ADMIN_NAME!"
) > backend\app\admin_config.py

echo ✅ Configuration admin enregistrée
echo.

:: ============================================================================
:: RÉCAPITULATIF
:: ============================================================================

echo ════════════════════════════════════════════════════════════════════
echo.
echo 📋 RÉCAPITULATIF DE LA CONFIGURATION
echo ════════════════════════════════════════════════════════════════════
echo.
echo 🗄️  Base de données:
echo    • Nom: !DB_NAME!
echo    • Utilisateur: !DB_USER!
echo    • Port: !POSTGRES_PORT!
echo.
echo 🌐 Accès:
echo    • Frontend: http://localhost:!FRONTEND_PORT!
echo    • API: http://localhost:!BACKEND_PORT!
echo    • API Docs: http://localhost:!BACKEND_PORT!/docs
echo.
echo 👤 Compte Admin:
echo    • Email: !ADMIN_EMAIL!
echo    • Mot de passe: !ADMIN_PASSWORD!
echo.
if "!IMAP_ENABLED!"=="true" (
echo 📧 Email IMAP: !IMAP_USER! sur !IMAP_SERVER!
) else (
echo 📧 Email IMAP: Non configuré
)
echo.
if "!SLACK_ENABLED!"=="true" (
echo 💬 Slack: Configuré
) else (
echo 💬 Slack: Non configuré
)
if "!DISCORD_ENABLED!"=="true" (
echo 🎮 Discord: Configuré
) else (
echo 🎮 Discord: Non configuré
)
if "!SMTP_ENABLED!"=="true" (
echo 📤 SMTP: Configuré via !SMTP_HOST!
) else (
echo 📤 SMTP: Non configuré
)
echo.
echo ════════════════════════════════════════════════════════════════════
echo.

:: ============================================================================
:: LANCEMENT
:: ============================================================================

echo Voulez-vous démarrer l'application maintenant ? (oui/non) [oui]:
set /p "start_now="
if /i "!start_now!"=="non" (
    echo.
    echo 👍 Configuration terminée !
    echo    Pour démarrer plus tard: double-cliquez sur quick-start.bat
    echo.
    pause
    exit /b 0
)

echo.
echo 🚀 Démarrage de l'application...
echo.

:: Build et démarrage
echo 📦 Construction des images Docker (peut prendre quelques minutes)...
docker-compose build

echo.
echo 🚀 Démarrage des services...
docker-compose up -d

echo.
echo ⏳ Attente du démarrage des services (20s)...
timeout /t 20 /nobreak >nul

:: Initialisation de la base
echo.
echo 📦 Initialisation de la base de données...
docker-compose exec -T backend python -m alembic upgrade head

echo.
echo 🌱 Création des données initiales...
docker-compose exec -T backend python -m app.db.seed

echo.
echo ════════════════════════════════════════════════════════════════════
echo.
echo  ✅ INSTALLATION TERMINÉE AVEC SUCCÈS !
echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                                                                    ║
echo ║   🌐 Ouvrez votre navigateur:                                     ║
echo ║      http://localhost:!FRONTEND_PORT!                                      ║
echo ║                                                                    ║
echo ║   👤 Connectez-vous avec:                                         ║
echo ║      Email: !ADMIN_EMAIL!
echo ║      Mot de passe: !ADMIN_PASSWORD!
echo ║                                                                    ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

:: Ouvrir le navigateur
start http://localhost:!FRONTEND_PORT!

echo.
echo 💡 Commandes utiles:
echo    • stop.bat      - Arrêter l'application
echo    • start.bat     - Menu de gestion
echo    • dev.bat       - Mode développement
echo.
echo Appuyez sur une touche pour voir les logs...
pause >nul
docker-compose logs -f

endlocal
