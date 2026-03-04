@echo off
title Autonomous Engineer — Stop
echo Stopping all Autonomous Engineer services...
docker compose down
echo Done. LibreChat services are untouched.
pause
