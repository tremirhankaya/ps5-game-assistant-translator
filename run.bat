@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Once setup.bat dosyasini calistir.
    pause
    exit /b 1
)
.venv\Scripts\python.exe -m ps5_translator
