@echo off
REM ===================================================================
REM  EvidenceCompare AI - stop the running app (Windows)
REM  Double-click to shut down the backend (:8000) and frontend (:3000).
REM ===================================================================
echo.
echo   Stopping EvidenceCompare AI...

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000" ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>&1

echo   Done. The app has been stopped.
echo   (You can close this window.)
timeout /t 4 >nul
