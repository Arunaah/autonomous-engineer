@echo off
echo ============================================================
echo  Autonomous Engineer — Windows Setup
echo ============================================================

echo [1/4] Copying .env file...
copy .env.example .env
echo Done. Edit .env with your API keys before continuing.
pause

echo [2/4] Starting Docker infrastructure...
docker-compose up -d postgres qdrant litellm
echo Waiting 15 seconds for services to start...
timeout /t 15

echo [3/4] Installing Python dependencies...
pip install -e ".[dev]"

echo [4/4] Verifying services...
docker-compose ps

echo ============================================================
echo  Setup complete!
echo  Next steps:
echo  1. Edit .env with your GLM5_API_KEY, MINIMAX_API_KEY, GITHUB_TOKEN
echo  2. Run: ae index-repo /path/to/your/repo
echo  3. Run: ae run --repo owner/repo --request "Your coding task"
echo ============================================================
pause
