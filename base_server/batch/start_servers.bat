@echo off
chcp 65001 >nul
echo ====================================
echo    SKN12 Server Start (Conda Env)
echo ====================================

cd /d C:\SKN12-FINAL-2TEAM\base_server

echo Conda environment check...
conda env list | findstr skn12
if %ERRORLEVEL% NEQ 0 (
    echo skn12 environment not found. Creating...
    conda create -n skn12 python=3.11 -y
    echo.
    echo Installing packages...
    call conda activate skn12
    pip install -r requirements.txt
    echo Environment setup complete!
) else (
    echo skn12 environment already exists.
    echo Checking and updating packages...
    call conda activate skn12
    pip install -r requirements.txt --upgrade-strategy only-if-needed
    echo Package update check complete!
)

echo.
echo Starting Base Web Server... (Port: 8000)
start "Base Web Server" cmd /k "chcp 65001 >nul && conda activate skn12 && uvicorn application.base_web_server.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Model Server... (Port: 8001)  
start "Model Server" cmd /k "chcp 65001 >nul && conda activate skn12 && uvicorn application.model_server.main:app --reload --host 0.0.0.0 --port 8001"

echo.
echo Both servers started in new windows:
echo - Base Web Server: http://localhost:8000
echo - Model Server: http://localhost:8001
echo - Environment: conda activate skn12
echo.
pause