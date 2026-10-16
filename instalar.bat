@echo off
rem Instala Pedrozilla 2.x en Windows (perfil Firefox + accesos directos).
rem Simplemente llama a instalar.ps1 con PowerShell.
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1"
set "RC=%ERRORLEVEL%"

rem Si se ha hecho doble clic, esperamos para que se lea el resultado.
rem Usa "instalar.bat --no-pause" para saltar la pausa.
if /i not "%~1"=="--no-pause" (
  echo %cmdcmdline% | find /i "%~nx0" >nul 2>nul && pause
)

exit /b %RC%
