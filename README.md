# Pedrozilla

Es un navegador basado en Chromium, es basicamente un chrome, pero intento que sea una slop pura y dura que come ram todo el dia

```
pedrozilla/                   <- el repositorio
├── README.md
├── requirements.txt         dependencias (PySide6)
├── crear_exe.bat            crea la aplicación dist\Pedrozilla\Pedrozilla.exe  (Windows)
├── pedrozilla_launcher.py   punto de entrada para empaquetar con PyInstaller
└── pedrozilla/              paquete del navegador
    ├── __init__.py
    ├── __main__.py          punto de entrada (python3 -m pedrozilla)
    ├── main.py              arranque, argumentos de línea de comandos y perfiles
    ├── browser.py           ventana: pestañas, barra de direcciones, menús, atajos
    ├── webview.py           QWebEngineView/QWebEnginePage (motor Chromium)
    ├── storage.py           ajustes, historial, marcadores y sesión (JSON)
    ├── downloads.py         descargas: seguimiento, barra inferior y diálogo
    ├── dialogs.py           historial, marcadores, ajustes y "acerca de"
    ├── newtab.py            HTML de la página de nueva pestaña
    ├── theme.py             hojas de estilo (tema oscuro y claro)
    ├── utils.py             parseo de la barra de direcciones y formateo
    ├── instalar.sh          icono + menú de aplicaciones + comando "pedrozilla"  (Linux)
    ├── instalar.bat/.ps1    icono + accesos directos  (Windows)
    ├── run.sh / run.bat     lanzadores
    └── libs/                librería de X11 que descarga instalar.sh (no se sube)
```

Las carpetas `build/`, `dist/` y las cachés de Python quedan fuera del control de
versiones (ver `.gitignore`).

## Requisitos

- Python 3.9 o superior
- PySide6 con Qt WebEngine (incluye su propia copia de Chromium)

Instalación de las dependencias:

```bash
python -m pip install -r requirements.txt
```

**Windows:** instala Python desde <https://www.python.org/downloads/> marcando
*Add python.exe to PATH*, y después:

```bat
python -m pip install PySide6
```

**Linux:** en lugar de `python` usa `python3`. En Ubuntu/Debian con Python
gestionado por el sistema (PEP 668) puede hacer falta:

```bash
python3 -m pip install --user --break-system-packages PySide6
```

En Linux, Qt 6 necesita además la librería `libxcb-cursor.so.0` para dibujar bajo
X11. Si tu distribución no la trae instalada, el instalador descarga una copia y
la guarda dentro del proyecto (`pedrozilla/libs/`), de modo que no hace
falta usar el administrador de paquetes. En Windows no hace falta nada de esto.

## Instalarlo en el escritorio

**Windows** — doble clic en `pedrozilla\instalar.bat` (o ejecútalo desde el
terminal). Esto genera el icono `pedrozilla.ico` y crea accesos directos en el
Escritorio (uno normal y otro de ventana privada) y en el menú Inicio:

```
pedrozilla\instalar.bat
```

**Linux** — un solo paso:

```bash
./pedrozilla/instalar.sh
```

Esto crea el icono, una entrada en el menú de aplicaciones, un acceso directo en el
escritorio y el comando `pedrozilla`. Después puedes abrirlo de tres maneras:

1. **Menú de aplicaciones** → busca «Pedrozilla» (categoría Internet).
2. **Doble clic** en `~/Escritorio/Pedrozilla.desktop`.
3. **Terminal** → `pedrozilla`

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
pedrozilla\run.bat "receta de tortilla"        :: abre una búsqueda
```

**Linux:**

```bash
cd "/home/pedrozilla/Documentos/Proyecto predeterminado"
./pedrozilla/run.sh                          # abre el navegador
./pedrozilla/run.sh example.com wikipedia.org  # abre direcciones al arrancar
./pedrozilla/run.sh --incognito              # ventana privada
./pedrozilla/run.sh --debug                  # muestra la consola JavaScript
./pedrozilla/run.sh "receta de tortilla"     # abre una búsqueda
```

En ambos casos también se puede lanzar como módulo (desde la carpeta que contiene
al paquete):

```bash
python -m pedrozilla https://example.com
```

## Crear una aplicación (.exe)

En Windows puedes empaquetar el navegador como una aplicación independiente, sin
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

Vuelve a ejecutar `crear_exe.bat` cada vez que cambies el código, porque la
aplicación incluye una copia del navegador en el momento de crearla.

Si `dist\Pedrozilla\Pedrozilla.exe` existe, `instalar.bat` hace que los accesos
directos del Escritorio y del menú Inicio apunten a él (así se abre como cualquier
otro programa, sin pasar por Python).

# Funciones

**Interfaz**
- Tema oscuro y claro; menú de aplicación, menú contextual completo (enlaces, imágenes,
  medios, texto seleccionado) y herramientas de desarrollo (`Ctrl+Shift+I`).

## Donde se guardan los datos

**Linux** (se respetan `XDG_CONFIG_HOME` y `XDG_DATA_HOME`):

- Ajustes, historial y marcadores: `~/.config/pedrozilla/`
- Perfil de Chromium (cookies, caché, almacenamiento web): `~/.local/share/pedrozilla/`
  (`profile/` y `cache/`; el perfil por defecto de Qt también se redirige ahí)
- Descargas: `~/Downloads` o la carpeta que elijas en Ajustes

**Windows:**

- Ajustes, historial y marcadores: `%APPDATA%\pedrozilla\`
- Perfil de Chromium (cookies, caché, almacenamiento web): `%LOCALAPPDATA%\pedrozilla\`
  (`profile/` y `cache/`; el perfil por defecto de Qt también se redirige ahí)
- Descargas: `%USERPROFILE%\Downloads` o la carpeta que elijas en Ajustes

Todo se borra desde *Ajustes → Avanzado → Borrar datos de navegación* o borrando
esas carpetas.

## Limitaciones conocidas

- No hay sincronización, extensiones ni lectura del formato de marcadores de Chrome.
- El bloqueo de anuncios, los gestores de contraseñas y las cuentas no están
  implementados.
- El menú contextual y las páginas internas son propios (no replican toda la
  funcionalidad de `chrome://`).
- Para reproducir vídeo con códecs propietarios (H.264) puede hacer falta la versión
  de Qt WebEngine del sistema en lugar de la de `pip`.

## Licencia

MIT. Puedes usar, modificar y distribuir Pedrozilla libremente; consulta el
archivo [LICENSE](LICENSE).
