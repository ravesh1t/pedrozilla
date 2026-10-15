@echo off
rem Crea la aplicacion independiente "dist\Pedrozilla\Pedrozilla.exe".
rem No necesita Python instalado para funcionar y puedes mover la carpeta
rem dist\Pedrozilla\ a donde quieras.
rem Vuelve a ejecutarlo cada vez que cambies el codigo.
setlocal

set "DIR=%~dp0"
pushd "%DIR%" || exit /b 1

rem Buscamos un Python con PySide6 (probamos "py", "python" y las rutas
rem habituales, por si el PATH de esta sesion aun no esta actualizado).
set "PY="
py -c "import PySide6.QtWebEngineWidgets" >nul 2>nul
if not errorlevel 1 set "PY=py"
if defined PY goto python_ok

python -c "import PySide6.QtWebEngineWidgets" >nul 2>nul
if not errorlevel 1 set "PY=python"
if defined PY goto python_ok

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if not defined PY (
        "%%D\python.exe" -c "import PySide6.QtWebEngineWidgets" >nul 2>nul
        if not errorlevel 1 set "PY="%%D\python.exe""
    )
)
if defined PY goto python_ok

echo Falta Python con PySide6 y Qt WebEngine.
echo Instala la dependencia con:
echo   python -m pip install PySide6
popd
exit /b 1

:python_ok
%PY% -m pip show pyinstaller >nul 2>nul
if not errorlevel 1 goto build

echo ==^> Instalando PyInstaller
%PY% -m pip install pyinstaller
if errorlevel 1 (
    echo ERROR: no se pudo instalar PyInstaller.
    popd
    exit /b 1
)

:build
echo ==^> Creando Pedrozilla.exe (puede tardar varios minutos)
%PY% -m PyInstaller --noconfirm --clean --windowed --name Pedrozilla --icon "pedrozilla\pedrozilla.ico" "pedrozilla_launcher.py"
if errorlevel 1 (
    echo ERROR: la creacion de la aplicacion ha fallado.
    popd
    exit /b 1
)

echo.
echo Listo: "%DIR%dist\Pedrozilla\Pedrozilla.exe"
echo Vuelve a ejecutar este archivo si cambias el codigo.
popd
exit /b 0
