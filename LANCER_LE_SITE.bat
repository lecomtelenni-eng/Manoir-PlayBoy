@echo off
setlocal
title Playboy Manor Manager
cd /d "%~dp0"

echo ============================================
echo       PLAYBOY MANOR MANAGER
echo ============================================
echo.

set "PYTHON_CMD="

where py >nul 2>nul
if %errorlevel%==0 set "PYTHON_CMD=py"

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if %errorlevel%==0 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo [ERREUR] Python n'est pas installe ou n'est pas ajoute au PATH.
    echo.
    echo Installe Python depuis python.org
    echo Pendant l'installation, coche obligatoirement :
    echo "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo Python detecte : %PYTHON_CMD%
echo Installation / verification de Flask...
%PYTHON_CMD% -m pip install --user -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERREUR] L'installation des dependances a echoue.
    echo Verifie ta connexion internet puis relance ce fichier.
    pause
    exit /b 1
)

echo.
echo Demarrage du serveur...
start "Playboy Manor Server" /min cmd /c "%PYTHON_CMD% app.py > serveur.log 2>&1"

echo Attente du demarrage...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$ok=$false; for($i=0;$i -lt 30;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/login -TimeoutSec 1; $ok=$true; break } catch {}; Start-Sleep -Seconds 1 }; if($ok){ exit 0 } else { exit 1 }"

if errorlevel 1 (
    echo.
    echo [ERREUR] Le serveur n'a pas demarre.
    echo Le fichier serveur.log contient le detail de l'erreur.
    echo.
    type serveur.log
    pause
    exit /b 1
)

echo Site pret.
start "" "http://127.0.0.1:5000/login"
echo.
echo Tu peux fermer cette fenetre.
timeout /t 3 >nul
exit
