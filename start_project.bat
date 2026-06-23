@echo off
title AI Startup Validator Launcher
echo ===================================================
echo   AI Startup Validator - Platform Launcher
echo ===================================================
echo.
echo Starting FastAPI Backend and Next.js Frontend...
echo.

:: 1. Launch FastAPI Backend
echo [1/2] Launching Backend Server on Port 8000...
start "Validator Backend API" cmd /k "cd backend && if not exist venv (echo Creating virtual environment... && python -m venv venv) && call venv\Scripts\activate && echo Installing dependencies... && pip install -r requirements.txt && echo Launching FastAPI... && uvicorn main:app --reload --port 8000"

:: 2. Launch Next.js Frontend
echo [2/2] Launching Frontend Server on Port 3000...
start "Validator Frontend App" cmd /k "cd frontend && echo Installing dependencies... && npm install && echo Launching Next.js... && npm run dev"

echo.
echo ===================================================
echo   Servers starting in separate command windows!
echo   - Backend API URL: http://localhost:8000
echo   - Frontend App URL: http://localhost:3000
echo ===================================================
echo.
pause
