@echo off
REM ===================================================================
REM  EvidenceCompare AI - REAL EVIDENCE, FREE (Windows)
REM  Pulls REAL, current studies from free public databases
REM  (PubMed, Europe PMC, ClinicalTrials.gov, FDA, Crossref) and writes
REM  the report with the built-in free synthesizer.
REM  No API keys, no payment. Needs an internet connection.
REM ===================================================================
setlocal
set "ROOT=%~dp0"

echo.
echo   Starting EvidenceCompare AI with REAL evidence (free)...
echo   Searches pull live studies from public medical databases.
echo.

REM --- Free the ports first so a re-launch is always clean
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000" ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>&1

REM --- Backend: real free evidence retrieval + free offline synthesis (no paid LLM)
start "EvidenceCompare API (REAL DATA)" /D "%ROOT%apps\api" cmd /k "set EVIDENCE_MODE=auto&& set LLM_MODE=offline&& .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"

REM --- Frontend (Next.js) on http://localhost:3000
start "EvidenceCompare Web" /D "%ROOT%apps\web" cmd /k "npm run dev"

echo   Waiting for the servers to warm up...
timeout /t 15 /nobreak >nul

echo   Opening http://localhost:3000 in your browser...
start "" http://localhost:3000

echo.
echo   ------------------------------------------------------------
echo   EvidenceCompare AI is running with REAL evidence (free).
echo     Web app : http://localhost:3000
echo     API     : http://localhost:8000/docs
echo   Reports now cite real PubMed/PMID + DOI sources per search.
echo   (First search may take ~10-20s while it queries the databases.)
echo.
echo   To STOP: close the two server windows (or run stop-app.bat).
echo   ------------------------------------------------------------
echo.
echo   You can close THIS window now.
timeout /t 8 >nul
