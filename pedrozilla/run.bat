@echo off
rem Lanzador de Pedrozilla para Windows.
rem Este script vive dentro del paquete pedrozilla\; el modulo se importa
rem desde la carpeta que lo contiene.
setlocal

set "DIR=%~dp0.."
pushd "%DIR%" || exit /b 1

rem Buscamos un Python que tenga PySide6 con Qt WebEngine. Se prueba primero el
rem lanzador "py" (evita el alias vacio de python.exe de la Microsoft Store) y,
rem si el PATH de esta sesion aun no esta actualizado, las rutas habituales.
set "PY="

py -c "import PySide6.QtWebEngineWidgets" >nul 2>nul
if not errorlevel 1 set "PY=py"
if defined PY goto launch

python -c "import PySide6.QtWebEngineWidgets" >nul 2>nul
if not errorlevel 1 set "PY=python"
if defined PY goto launch

if exist "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" (
    "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" -c "import PySide6.QtWebEngineWidgets" >nul 2>nul
    if not errorlevel 1 set "PY="%LOCALAPPDATA%\Programs\Python\Launcher\py.exe""
)
if defined PY goto launch

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if not defined PY (
        "%%D\python.exe" -c "import PySide6.QtWebEngineWidgets" >nul 2>nul
        if not errorlevel 1 set "PY="%%D\python.exe""
    )
)
if defined PY goto launch

echo Falta Python con PySide6 y Qt WebEngine.
echo.
echo Si ya tienes Python instalado, instala la dependencia con:
echo   python -m pip install PySide6
echo.
echo Si aun no tienes Python: https://www.python.org/downloads/
echo Despues vuelve a ejecutar este archivo.
popd
exit /b 1

:launch
%PY% -m pedrozilla %*
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
