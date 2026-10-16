@echo off
rem Lanzador de Pedrozilla 2.x para Windows (distribucion basada en Firefox).
rem Usa un perfil propio (%APPDATA%\pedrozilla\firefox-profile) para no tocar
rem el perfil normal de Firefox. No necesita Python ni administrador.
setlocal EnableDelayedExpansion

set "DIR=%~dp0"
set "VERSION_FILE=%DIR%VERSION"
set "PZVERSION=desconocida"
if exist "%VERSION_FILE%" set /p PZVERSION=<"%VERSION_FILE%"

rem --version: no hace falta Firefox.
echo %* | findstr /i /c:"--version" >nul 2>nul
if not errorlevel 1 (
    echo Pedrozilla %PZVERSION%
    exit /b 0
)

rem Localiza firefox.exe.
set "FF="
if exist "%ProgramFiles%\Mozilla Firefox\firefox.exe" set "FF=%ProgramFiles%\Mozilla Firefox\firefox.exe"
if not defined FF if exist "%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe" set "FF=%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe"
if not defined FF (
    for /f "delims=" %%F in ('where firefox 2^>nul') do (
        if not defined FF set "FF=%%F"
    )
)
if not defined FF (
    echo Falta Firefox. Instalalo desde https://www.mozilla.org/firefox/ y vuelve a intentarlo.
    exit /b 1
)

rem Prepara el perfil (idempotente).
set "PROFILE=%APPDATA%\pedrozilla\firefox-profile"
powershell -NoProfile -ExecutionPolicy Bypass -File "%DIR%tools\init-profile.ps1" -ProfileDir "%PROFILE%" -SkeletonDir "%DIR%firefox-profile-skeleton" -NewTabSource "%DIR%newtab\index.html" >nul
if errorlevel 1 (
    echo ERROR: no se pudo preparar el perfil en %PROFILE%.
    exit /b 1
)

rem Argumentos: --incognito (o -i) abre ventana privada; el resto se pasa a Firefox.
set "PRIVATE="
set "URLS="
for %%A in (%*) do (
    set "ARG=%%~A"
    if /i "!ARG!"=="--incognito" (
        set "PRIVATE=-private-window"
    ) else if /i "!ARG!"=="-i" (
        set "PRIVATE=-private-window"
    ) else (
        set "URLS=!URLS! %%A"
    )
)

if defined PRIVATE (
    start "" "%FF%" -profile "%PROFILE%" -private-window %URLS%
) else (
    start "" "%FF%" -profile "%PROFILE%" %URLS%
)
exit /b 0
