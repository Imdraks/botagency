        @echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Configuration Gmail pour Opportunities Radar

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║           📧 CONFIGURATION GMAIL - INGESTION EMAILS               ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

echo ┌────────────────────────────────────────────────────────────────────┐
echo │  ÉTAPE 1: Activer IMAP dans Gmail                                 │
echo ├────────────────────────────────────────────────────────────────────┤
echo │                                                                    │
echo │  1. Ouvrez Gmail dans votre navigateur                            │
echo │  2. Cliquez sur ⚙️ Paramètres → Voir tous les paramètres          │
echo │  3. Onglet "Transfert et POP/IMAP"                                │
echo │  4. Activez "Activer IMAP"                                        │
echo │  5. Enregistrez                                                   │
echo │                                                                    │
echo └────────────────────────────────────────────────────────────────────┘
echo.
echo Appuyez sur une touche quand c'est fait...
pause >nul

echo.
echo ┌────────────────────────────────────────────────────────────────────┐
echo │  ÉTAPE 2: Créer un mot de passe d'application                     │
echo ├────────────────────────────────────────────────────────────────────┤
echo │                                                                    │
echo │  ⚠️  Google n'autorise plus les mots de passe normaux !           │
echo │                                                                    │
echo │  1. Allez sur: https://myaccount.google.com/apppasswords          │
echo │  2. Connectez-vous si demandé                                     │
echo │  3. En bas, cliquez "Sélectionner une application" → "Autre"      │
echo │  4. Tapez "Opportunities Radar"                                   │
echo │  5. Cliquez "Générer"                                             │
echo │  6. Copiez le mot de passe de 16 caractères (sans espaces)        │
echo │                                                                    │
echo └────────────────────────────────────────────────────────────────────┘
echo.
echo J'ouvre la page Google pour vous...
start https://myaccount.google.com/apppasswords
echo.
echo Appuyez sur une touche quand vous avez le mot de passe...
pause >nul

echo.
echo ┌────────────────────────────────────────────────────────────────────┐
echo │  ÉTAPE 3: Configuration                                           │
echo └────────────────────────────────────────────────────────────────────┘
echo.

set /p "GMAIL_EMAIL=Votre adresse Gmail: "
set /p "GMAIL_APP_PASSWORD=Mot de passe d'application (16 car.): "

echo.
echo Quel dossier Gmail surveiller ?
echo   1. INBOX (Boîte de réception)
echo   2. Un label spécifique (ex: NEWSLETTERS)
echo.
set /p "folder_choice=Votre choix [1]: "

if "!folder_choice!"=="2" (
    echo.
    echo 💡 Conseil: Créez un filtre Gmail pour classer automatiquement
    echo    les emails de newsletters dans un label dédié.
    echo.
    set /p "GMAIL_FOLDER=Nom du label Gmail: "
) else (
    set "GMAIL_FOLDER=INBOX"
)

echo.
echo ────────────────────────────────────────────────────────────────────
echo.
echo 📝 Mise à jour du fichier .env...

:: Vérifier si .env existe
if not exist .env (
    echo ❌ Fichier .env non trouvé. Lancez d'abord install.bat
    pause
    exit /b 1
)

:: Créer un fichier temporaire avec les nouvelles valeurs
set "tempfile=%TEMP%\env_update_%RANDOM%.txt"

:: Lire le .env et mettre à jour les lignes IMAP
(
    for /f "usebackq tokens=* delims=" %%a in (".env") do (
        set "line=%%a"
        
        echo !line! | findstr /b "IMAP_ENABLED=" >nul
        if not errorlevel 1 (
            echo IMAP_ENABLED=true
        ) else (
            echo !line! | findstr /b "IMAP_SERVER=" >nul
            if not errorlevel 1 (
                echo IMAP_SERVER=imap.gmail.com
            ) else (
                echo !line! | findstr /b "IMAP_PORT=" >nul
                if not errorlevel 1 (
                    echo IMAP_PORT=993
                ) else (
                    echo !line! | findstr /b "IMAP_USER=" >nul
                    if not errorlevel 1 (
                        echo IMAP_USER=!GMAIL_EMAIL!
                    ) else (
                        echo !line! | findstr /b "IMAP_PASSWORD=" >nul
                        if not errorlevel 1 (
                            echo IMAP_PASSWORD=!GMAIL_APP_PASSWORD!
                        ) else (
                            echo !line! | findstr /b "IMAP_FOLDER=" >nul
                            if not errorlevel 1 (
                                echo IMAP_FOLDER=!GMAIL_FOLDER!
                            ) else (
                                echo !line!
                            )
                        )
                    )
                )
            )
        )
    )
) > "!tempfile!"

:: Remplacer le .env
move /y "!tempfile!" .env >nul

echo ✅ Configuration Gmail enregistrée
echo.

:: Redémarrer les services si Docker tourne
docker-compose ps >nul 2>&1
if not errorlevel 1 (
    echo 🔄 Redémarrage des services pour appliquer la config...
    docker-compose restart backend worker
    echo ✅ Services redémarrés
)

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                    ✅ GMAIL CONFIGURÉ !                           ║
echo ╠════════════════════════════════════════════════════════════════════╣
echo ║                                                                    ║
echo ║   📧 Email: !GMAIL_EMAIL!
echo ║   📁 Dossier: !GMAIL_FOLDER!
echo ║                                                                    ║
echo ║   L'ingestion email va maintenant collecter automatiquement       ║
echo ║   les opportunités depuis votre boîte Gmail.                      ║
echo ║                                                                    ║
echo ║   💡 Conseil: Créez un filtre Gmail pour classer les newsletters  ║
echo ║      dans un label dédié (ex: "OPPORTUNITIES")                    ║
echo ║                                                                    ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.
pause

endlocal
