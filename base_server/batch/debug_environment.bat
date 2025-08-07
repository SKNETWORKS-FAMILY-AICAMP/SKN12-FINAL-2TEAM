@echo off
chcp 65001 >nul
echo ====================================
echo    Environment Debug Information
echo ====================================

cd /d C:\SKN12-FINAL-2TEAM\base_server

echo 1. Current Directory:
echo %CD%

echo.
echo 2. Python Version:
python --version 2>nul || echo Python not found in PATH

echo.
echo 3. Conda Version:
conda --version 2>nul || echo Conda not found

echo.
echo 4. Available Conda Environments:
conda env list 2>nul || echo Failed to list environments

echo.
echo 5. Port Usage Check:
echo Port 8000:
netstat -an | findstr :8000 || echo Port 8000 is free
echo Port 8001:
netstat -an | findstr :8001 || echo Port 8001 is free

echo.
echo 6. Testing conda activation:
call conda activate skn12 2>nul && echo SUCCESS: skn12 environment activated || echo FAILED: Cannot activate skn12

echo.
echo 7. Python packages check (if environment active):
pip list | findstr -i "fastapi uvicorn" 2>nul || echo FastAPI/Uvicorn not found

echo.
echo 8. File permissions check:
dir application\base_web_server\main.py >nul 2>nul && echo Base server main.py exists || echo Base server main.py missing
dir application\model_server\main.py >nul 2>nul && echo Model server main.py exists || echo Model server main.py missing

echo.
echo ====================================
echo    Debug Complete
echo ====================================
pause