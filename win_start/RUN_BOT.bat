@echo off
cd /d "%~dp0.."
title Telegram Bot Engine
setlocal enabledelayedexpansion

set "PYTHON_DIR=%cd%\python_portable"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

if exist "%PYTHON_EXE%" (
    goto :run_bot
)

echo [*] Portable Python not found. Starting automatic setup...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile 'python_embed.zip'"
powershell -Command "Expand-Archive -Path 'python_embed.zip' -DestinationPath '%PYTHON_DIR%'"
del python_embed.zip

if exist "%PYTHON_DIR%\python311._pth" (
    powershell -Command "(Get-Content '%PYTHON_DIR%\python311._pth') -replace '#import site', 'import site' | Set-Content '%PYTHON_DIR%\python311._pth'"
)

powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
"%PYTHON_EXE%" get-pip.py --no-warn-script-location >nul 2>&1
del get-pip.py

echo [*] Installing dependencies from requirements.txt...
"%PYTHON_EXE%" -m pip install --no-warn-script-location -r requirements.txt
echo [OK] Setup complete!

:run_bot
echo [*] Starting Telegram Bot...
"%PYTHON_EXE%" main.py
pause