@echo off
chcp 65001 >nul
echo.
echo 🛑 Arrêt de Opportunities Radar...
docker-compose down
echo ✅ Tous les services sont arrêtés
echo.
pause
