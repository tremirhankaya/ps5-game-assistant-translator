@echo off
rem One-step setup: installs Python 3.13 if needed, creates .venv and installs packages.
rem Python 3.13 is used because onnxruntime (needed by RapidOCR) has no build for newer versions yet.
setlocal
cd /d "%~dp0"

set "PY="
py -3.13 -c "" >nul 2>&1 && set "PY=py -3.13"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PY="%LOCALAPPDATA%\Programs\Python\Python313\python.exe""

if not defined PY (
    echo Python 3.13 bulunamadi, winget ile kuruluyor...
    winget install --id Python.Python.3.13 -e --scope user --accept-package-agreements --accept-source-agreements
    if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PY="%LOCALAPPDATA%\Programs\Python\Python313\python.exe""
)
if not defined PY (
    echo.
    echo HATA: Python 3.13 kurulamadi. python.org adresinden 3.13 surumunu elle kurup bu dosyayi tekrar calistir.
    pause
    exit /b 1
)

echo Sanal ortam olusturuluyor (.venv)...
%PY% -m venv --clear .venv || goto :fail
echo Paketler kuruluyor (birkac dakika surebilir)...
.venv\Scripts\python.exe -m pip install --upgrade pip >nul
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt || goto :fail

echo.
echo Kurulum tamam. Uygulamayi acmak icin run.bat dosyasini calistir.
pause
exit /b 0

:fail
echo.
echo HATA: Kurulum tamamlanamadi. Yukaridaki mesaji kontrol et.
pause
exit /b 1
