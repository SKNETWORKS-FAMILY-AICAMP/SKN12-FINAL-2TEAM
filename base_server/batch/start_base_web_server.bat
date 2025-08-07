@echo off
echo ====================================
echo    SKN12 Base Web Server 시작
echo ====================================
cd /d "%~dp0"
cd ..
echo 현재 디렉토리: %CD%
echo.
echo Base Web Server 실행 중... (Port: 8000)
echo 종료하려면 Ctrl+C를 누르세요
echo.
uvicorn application.base_web_server.main:app --reload --host 0.0.0.0 --port 8000 --reload-exclude frontend/
pause