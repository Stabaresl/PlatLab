@echo off
rem Doble clic para instalar o actualizar PlatLAB en Windows.
rem Equivale a: powershell -ExecutionPolicy Bypass -File platlab.ps1 instalar
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0platlab.ps1" %*
echo.
pause
