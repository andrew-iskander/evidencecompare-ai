@echo off
REM ===================================================================
REM  EvidenceCompare AI - one-click launcher (Windows)
REM  Double-click this file to start the app and open it in your browser.
REM ===================================================================
setlocal
set "ROOT=%~dp0"

echo.
echo   Starting EvidenceCompare AI...
echo   (two windows will open - leave them running while you use the app)
echo.

REM --- Free the ports first so a re-launch is always clean
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000" ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>&1

REM --- Backend (FastAPI) on http://localhost:8000, offline mode (no API keys needed)
start "EvidenceCompare API" /D "%ROOT%apps\api" cmd /k "set EVIDENCE_MODE=offline&& set LLM_MODE=offline&& .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"

REM --- Frontend (Next.js) on http://localhost:3000
start "EvidenceCompare Web" /D "%ROOT%apps\web" cmd /k "npm run dev"

echo   Waiting for the servers to warm up...
timeout /t 15 /nobreak >nul

echo   Opening http://localhost:3000 in your browser...
start "" http://localhost:3000

echo.
echo   ------------------------------------------------------------
echo   EvidenceCompare AI is running.
echo     Web app : http://localhost:3000
echo     API     : http://localhost:8000/docs
echo.
echo   To STOP: close the two windows titled "EvidenceCompare API"
echo   and "EvidenceCompare Web" (or run stop-app.bat).
echo   ------------------------------------------------------------
echo.
echo   You can close THIS window now.
timeout /t 8 >nul
