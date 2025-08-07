@echo off
echo ====================================
echo    SKN12 Model Server 시작
echo ====================================
cd /d "%~dp0"
cd ..
echo 현재 디렉토리: %CD%
echo.
echo Model Server 실행 중... (Port: 8001)
echo 종료하려면 Ctrl+C를 누르세요
echo.
uvicorn application.model_server.main:app --reload --host 0.0.0.0 --port 8001
pause