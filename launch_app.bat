@echo off
echo.
echo ===========================================
echo Tally Expert AI - Development Launcher
echo ===========================================
echo.
echo [1] Start AI Backend (FastAPI on Port 8000)
echo [2] Start React Frontend (Vite on Port 5173)
echo [3] Full System Cleanup (Git)
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo Starting Backend...
    .\tallyenv\Scripts\python server.py
)
if "%choice%"=="2" (
    echo Starting Frontend...
    cd frontend
    npm run dev
)
if "%choice%"=="3" (
    echo Cleaning up...
    git rm -r --cached node_modules
    git add .
    git commit -m "chore: repository cleanup"
    echo Done!
)
pause
