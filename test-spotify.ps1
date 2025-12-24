# Script de test rapide de l'API Spotify
# Usage: .\test-spotify.ps1

Write-Host "🎵 Test de l'integration Spotify API" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier que spotipy est installé
Write-Host "1. Verification de spotipy..." -ForegroundColor Yellow
$spotipyCheck = docker exec radar_backend pip show spotipy 2>&1
if ($spotipyCheck -match "Name: spotipy") {
    Write-Host "   ✅ spotipy est installe (version $($spotipyCheck -match 'Version: (.*)' | Out-Null; $Matches[1]))" -ForegroundColor Green
} else {
    Write-Host "   ❌ spotipy n'est pas installe" -ForegroundColor Red
    Write-Host "   → Executez: docker-compose build --no-cache backend worker" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Vérifier les variables d'environnement
Write-Host "2. Verification des variables d'environnement..." -ForegroundColor Yellow
$clientId = docker exec radar_backend printenv SPOTIFY_CLIENT_ID 2>&1
$clientSecret = docker exec radar_backend printenv SPOTIFY_CLIENT_SECRET 2>&1

if ($clientId -and $clientId -ne "" -and $clientSecret -and $clientSecret -ne "") {
    Write-Host "   ✅ SPOTIFY_CLIENT_ID: $($clientId.Substring(0, [Math]::Min(8, $clientId.Length)))..." -ForegroundColor Green
    Write-Host "   ✅ SPOTIFY_CLIENT_SECRET: $($clientSecret.Substring(0, [Math]::Min(8, $clientSecret.Length)))..." -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Variables Spotify non configurees" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Pour configurer:" -ForegroundColor Cyan
    Write-Host "   1. Creer un fichier .env a la racine du projet" -ForegroundColor White
    Write-Host "   2. Ajouter:" -ForegroundColor White
    Write-Host "      SPOTIFY_CLIENT_ID=votre_client_id" -ForegroundColor Gray
    Write-Host "      SPOTIFY_CLIENT_SECRET=votre_client_secret" -ForegroundColor Gray
    Write-Host "   3. Redemarrer: docker-compose restart backend worker" -ForegroundColor White
    Write-Host ""
    Write-Host "   📚 Guide complet: SPOTIFY_API_SETUP.md" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host ""

# Test Python du client Spotify
Write-Host "3. Test du client Spotify..." -ForegroundColor Yellow
$testScript = @'
from app.intelligence.spotify_client import spotify_client
if spotify_client.is_available():
    print("✅ Client Spotify initialise avec succes")
    # Test avec un artiste connu
    result = spotify_client.search_artist("Nayra")
    if result:
        print(f"✅ Test de recherche OK: {result['name']} - {result['followers']:,} followers")
    else:
        print("⚠️  Artiste non trouve (normal si nom incorrect)")
else:
    print("❌ Client Spotify non disponible (credentials manquants)")
'@

$testResult = docker exec radar_backend python -c $testScript 2>&1
Write-Host "   $testResult" -ForegroundColor $(if ($testResult -match "✅") { "Green" } elseif ($testResult -match "⚠️") { "Yellow" } else { "Red" })

Write-Host ""

# Vérifier les logs
Write-Host "4. Verification des logs recents..." -ForegroundColor Yellow
$logs = docker logs radar_backend --tail 50 2>&1 | Select-String "Spotify"
if ($logs) {
    Write-Host "   Logs Spotify trouves:" -ForegroundColor Green
    $logs | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "   ℹ️  Aucun log Spotify recent" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Test termine !" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 Documentation: SPOTIFY_API_SETUP.md" -ForegroundColor White
Write-Host "🚀 Pour tester dans l'interface: http://localhost:3000/dashboard" -ForegroundColor White
Write-Host ""
