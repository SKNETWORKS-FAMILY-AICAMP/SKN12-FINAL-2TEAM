@echo off
chcp 65001 >nul
echo ====================================
echo    SKN12 Conda Environment Setup
echo ====================================

cd /d C:\SKN12-FINAL-2TEAM\base_server

echo 1. Creating Conda environment... (Python 3.11)
conda create -n skn12 python=3.11 -y

echo.
echo 2. Activating environment and installing packages...
call conda activate skn12
pip install -r requirements.txt

echo.
echo 3. Environment setup complete!
echo.
echo Usage:
echo - Activate environment: conda activate skn12
echo - Start servers: run start_servers.bat
echo.
pause