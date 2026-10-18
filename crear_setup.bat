@echo off
rem Crea el instalador dist\PedrozillaSetup-1.1.0.exe (un solo archivo).
rem 1) Genera dist\Pedrozilla\ con crear_exe.bat (necesita Python una vez).
rem 2) Lo empaqueta con NSIS (makensis en PATH o en %LOCALAPPDATA%\scoop).
rem El instalador resultante NO necesita Python ni admin para usarse.
setlocal

set "DIR=%~dp0"
pushd "%DIR%" || exit /b 1

if not exist "dist\Pedrozilla\Pedrozilla.exe" (
    echo ==^> Generando dist\Pedrozilla
    call crear_exe.bat
    if errorlevel 1 (
        echo ERROR: fallo crear_exe.bat.
        popd
        exit /b 1
    )
) else (
    echo ==^> Reutilizando dist\Pedrozilla existente
)

set "NSIS="
where makensis >nul 2>nul
if not errorlevel 1 set "NSIS=makensis"
if not defined NSIS if exist "%LOCALAPPDATA%\scoop\apps\nsis\current\makensis.exe" set "NSIS=%LOCALAPPDATA%\scoop\apps\nsis\current\makensis.exe"
if not defined NSIS (
    for /d %%D in ("%LOCALAPPDATA%\scoop\apps\nsis\*") do (
        if not defined NSIS if exist "%%D\makensis.exe" set "NSIS=%%D\makensis.exe"
    )
)
if not defined NSIS (
    echo Falta NSIS. Instalalo con:
    echo   scoop bucket add extras ^& scoop install nsis
    popd
    exit /b 1
)

echo ==^> Creando instalador con "%NSIS%"
rem Ruta absoluta: con ruta relativa ${__FILEDIR__} resuelve mal y no encuentra el icono.
"%NSIS%" "%DIR%installer\pedrozilla.nsi"
if errorlevel 1 (
    echo ERROR: fallo makensis.
    popd
    exit /b 1
)

echo.
echo Listo: "%DIR%dist\PedrozillaSetup-1.1.0.exe"
popd
exit /b 0
