# Pedrozilla

> **1.1.0**: extensiones Chromium (MV3) y limpieza del repo. La etapa Firefox
> vive en la rama `firefox-concept`.

Es un navegador basado en Chromium, es basicamente un chrome, pero intento que sea una slop pura y dura que come ram todo el dia

```
pedrozilla/                   <- el repositorio
Ôö£ÔöÇÔöÇ README.md
Ôö£ÔöÇÔöÇ requirements.txt         dependencias (PySide6)
Ôö£ÔöÇÔöÇ crear_exe.bat            crea la aplicaci├│n dist\Pedrozilla\Pedrozilla.exe  (Windows)
Ôö£ÔöÇÔöÇ pedrozilla_launcher.py   punto de entrada para empaquetar con PyInstaller
ÔööÔöÇÔöÇ pedrozilla/              paquete del navegador
    Ôö£ÔöÇÔöÇ __init__.py
    Ôö£ÔöÇÔöÇ __main__.py          punto de entrada (python3 -m pedrozilla)
    Ôö£ÔöÇÔöÇ main.py              arranque, argumentos de l├¡nea de comandos y perfiles
    Ôö£ÔöÇÔöÇ browser.py           ventana: pesta├▒as, barra de direcciones, men├║s, atajos
    Ôö£ÔöÇÔöÇ webview.py           QWebEngineView/QWebEnginePage (motor Chromium)
    Ôö£ÔöÇÔöÇ storage.py           ajustes, historial, marcadores y sesi├│n (JSON)
    Ôö£ÔöÇÔöÇ downloads.py         descargas: seguimiento, barra inferior y di├ílogo
    Ôö£ÔöÇÔöÇ dialogs.py           historial, marcadores, ajustes y "acerca de"
    Ôö£ÔöÇÔöÇ newtab.py            HTML de la p├ígina de nueva pesta├▒a
    Ôö£ÔöÇÔöÇ theme.py             hojas de estilo (tema cl├ísico tipo Firefox 7, oscuro y claro)
    Ôö£ÔöÇÔöÇ utils.py             parseo de la barra de direcciones y formateo
    Ôö£ÔöÇÔöÇ instalar.sh          icono + men├║ de aplicaciones + comando "pedrozilla"  (Linux)
    Ôö£ÔöÇÔöÇ instalar.bat/.ps1    icono + accesos directos  (Windows)
    Ôö£ÔöÇÔöÇ run.sh / run.bat     lanzadores
    ÔööÔöÇÔöÇ libs/                librer├¡a de X11 que descarga instalar.sh (no se sube)
```

Las carpetas `build/`, `dist/` y las cach├®s de Python quedan fuera del control de
versiones (ver `.gitignore`).

## Requisitos

- Python 3.9 o superior
- PySide6 con Qt WebEngine (incluye su propia copia de Chromium)

Instalaci├│n de las dependencias:

```bash
python -m pip install -r requirements.txt
```

**Windows:** instala Python desde <https://www.python.org/downloads/> marcando
*Add python.exe to PATH*, y despu├®s:

```bat
python -m pip install PySide6
```

**Linux:** en lugar de `python` usa `python3`. En Ubuntu/Debian con Python
gestionado por el sistema (PEP 668) puede hacer falta:

```bash
python3 -m pip install --user --break-system-packages PySide6
```

En Linux, Qt 6 necesita adem├ís la librer├¡a `libxcb-cursor.so.0` para dibujar bajo
X11. Si tu distribuci├│n no la trae instalada, el instalador descarga una copia y
la guarda dentro del proyecto (`pedrozilla/libs/`), de modo que no hace
falta usar el administrador de paquetes. En Windows no hace falta nada de esto.

## Instalarlo en el escritorio

**Windows** ÔÇö doble clic en `pedrozilla\instalar.bat` (o ejec├║talo desde el
terminal). Esto genera el icono `pedrozilla.ico` y crea accesos directos en el
Escritorio (uno normal y otro de ventana privada) y en el men├║ Inicio:

```
pedrozilla\instalar.bat
```

**Linux** ÔÇö un solo paso:

```bash
./pedrozilla/instalar.sh
```

Esto crea el icono, una entrada en el men├║ de aplicaciones, un acceso directo en el
escritorio y el comando `pedrozilla`. Despu├®s puedes abrirlo de tres maneras:

1. **Men├║ de aplicaciones** ÔåÆ busca ┬½Pedrozilla┬╗ (categor├¡a Internet).
2. **Doble clic** en `~/Escritorio/Pedrozilla.desktop`.
3. **Terminal** ÔåÆ `pedrozilla`

Vuelve a ejecutar el instalador si mueves la carpeta del proyecto (en Windows,
`pythonw.exe` se queda enganchado a la ruta del proyecto).

## Uso

**Windows:**

```bat
cd "D:\opencode pruebas\pedrozilla"
pedrozilla\run.bat                            :: abre el navegador
pedrozilla\run.bat example.com wikipedia.org   :: abre direcciones al arrancar
pedrozilla\run.bat --incognito                 :: ventana privada
pedrozilla\run.bat --debug                     :: muestra la consola JavaScript
pedrozilla\run.bat "receta de tortilla"        :: abre una b├║squeda
```

**Linux:**

```bash
cd "/home/pedrozilla/Documentos/Proyecto predeterminado"
./pedrozilla/run.sh                          # abre el navegador
./pedrozilla/run.sh example.com wikipedia.org  # abre direcciones al arrancar
./pedrozilla/run.sh --incognito              # ventana privada
./pedrozilla/run.sh --debug                  # muestra la consola JavaScript
./pedrozilla/run.sh "receta de tortilla"     # abre una b├║squeda
```

En ambos casos tambi├®n se puede lanzar como m├│dulo (desde la carpeta que contiene
al paquete):

```bash
python -m pedrozilla https://example.com
```

## Crear una aplicaci├│n (.exe)

En Windows puedes empaquetar el navegador como una aplicaci├│n independiente, sin
necesidad de tener Python instalado para usarla:

```bat
crear_exe.bat
```

Esto genera `dist\Pedrozilla\Pedrozilla.exe` (necesita PyInstaller, que el script
instala solo la primera vez). La carpeta `dist\Pedrozilla\` es autosuficiente:
puedes moverla a donde quieras y llevarla en un pendrive. Acepta los mismos
argumentos que el resto de lanzadores:

```bat
dist\Pedrozilla\Pedrozilla.exe --incognito
dist\Pedrozilla\Pedrozilla.exe ejemplo.com
```

Vuelve a ejecutar `crear_exe.bat` cada vez que cambies el c├│digo, porque la
aplicaci├│n incluye una copia del navegador en el momento de crearla.

Si `dist\Pedrozilla\Pedrozilla.exe` existe, `instalar.bat` hace que los accesos
directos del Escritorio y del men├║ Inicio apunten a ├®l (as├¡ se abre como cualquier
otro programa, sin pasar por Python).

## Instalador para otros PCs (sin Python)

Si quieres pasárselo a alguien que no tiene (o no quiere) Python:

```bat
crear_setup.bat
```

Genera `dist\PedrozillaSetup-1.1.0.exe`: un único archivo que instala
Pedrozilla en `%LOCALAPPDATA%\Pedrozilla`, crea los accesos directos y lo
registra para desinstalarlo desde *Configuración → Aplicaciones*.
No pide Python ni administrador. Pásale ese `.exe` a tu amigo y listo.

# Funciones

**Interfaz**
- Aspecto **cl├ísico tipo Firefox 7** (pesta├▒as arriba, bot├│n naranja de men├║ y una sola
  barra de direcciones, sin caja de b├║squeda aparte); tambi├®n hay temas oscuro y claro.
  Men├║ de aplicaci├│n, men├║ contextual completo (enlaces, im├ígenes,
  medios, texto seleccionado) y herramientas de desarrollo (`Ctrl+Shift+I`).

## Donde se guardan los datos

**Linux** (se respetan `XDG_CONFIG_HOME` y `XDG_DATA_HOME`):

- Ajustes, historial y marcadores: `~/.config/pedrozilla/`
- Perfil de Chromium (cookies, cach├®, almacenamiento web): `~/.local/share/pedrozilla/`
  (`profile/` y `cache/`; el perfil por defecto de Qt tambi├®n se redirige ah├¡)
- Descargas: `~/Downloads` o la carpeta que elijas en Ajustes

**Windows:**

- Ajustes, historial y marcadores: `%APPDATA%\pedrozilla\`
- Perfil de Chromium (cookies, cach├®, almacenamiento web): `%LOCALAPPDATA%\pedrozilla\`
  (`profile/` y `cache/`; el perfil por defecto de Qt tambi├®n se redirige ah├¡)
- Descargas: `%USERPROFILE%\Downloads` o la carpeta que elijas en Ajustes

Todo se borra desde *Ajustes ÔåÆ Avanzado ÔåÆ Borrar datos de navegaci├│n* o borrando
esas carpetas.

## Limitaciones conocidas

- No hay sincronizaci├│n, extensiones ni lectura del formato de marcadores de Chrome.
- El bloqueo de anuncios, los gestores de contrase├▒as y las cuentas no est├ín
  implementados.
- El men├║ contextual y las p├íginas internas son propios (no replican toda la
  funcionalidad de `chrome://`).
- Para reproducir v├¡deo con c├│decs propietarios (H.264) puede hacer falta la versi├│n
  de Qt WebEngine del sistema en lugar de la de `pip`.

## Licencia

MIT. Puedes usar, modificar y distribuir Pedrozilla libremente; consulta el
archivo [LICENSE](LICENSE).
