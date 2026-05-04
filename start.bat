@echo off
REM RAbot production startup script (Windows)
cd /d "%~dp0"

echo === Building frontend ===
cd frontend
call npx vite build
if %errorlevel% neq 0 (
    echo Frontend build failed.
    pause
    exit /b %errorlevel%
)
cd ..

echo.
echo === Starting backend on http://0.0.0.0:8000 ===
set PYTHONPATH=%cd%\src
uvicorn backend.main:app --host 0.0.0.0 --port 8000
pause
