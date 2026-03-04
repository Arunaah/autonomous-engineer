@echo off
title Autonomous Engineer — Startup
echo.
echo ============================================================
echo   AUTONOMOUS ENGINEER — PLUG AND PLAY STARTUP
echo ============================================================
echo.

REM Check Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker is not running. Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo [*] Waiting 30 seconds for Docker to start...
    timeout /t 30 /nobreak >nul
)

echo [1/5] Pulling latest images...
docker compose pull --quiet

echo [2/5] Starting all services...
docker compose up -d --build

echo [3/5] Waiting for services to be healthy...
timeout /t 15 /nobreak >nul

echo [4/5] Checking GLM-4 model...
docker exec ae-ollama ollama list | findstr "glm4" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] GLM-4 not found. Pulling now (5.5GB — please wait)...
    docker exec ae-ollama ollama pull glm4
) else (
    echo [*] GLM-4 already installed.
)

echo [5/5] Verifying all services...
curl -s http://localhost:8000/health
echo.

echo ============================================================
echo   ALL SYSTEMS READY
echo ============================================================
echo.
echo   API:        http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo   LiteLLM:    http://localhost:4000
echo   LibreChat:  http://localhost:3080
echo.
echo   To submit a coding task:
echo   curl -X POST http://localhost:8000/build ^
echo        -H "Content-Type: application/json" ^
echo        -d "{\"request\": \"your coding task here\"}"
echo.
echo   Then check status:
echo   curl http://localhost:8000/status/1
echo.
pause
