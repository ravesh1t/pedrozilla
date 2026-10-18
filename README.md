# Pedrozilla

> **1.1.0** — navegador de escritorio basado en Chromium (Qt WebEngine).

Slop pura y dura que come RAM todo el día: Chromium metido en Python (PySide6),
con interfaz clásica tipo Firefox 7. Sin cuentas ni sincronización.

## Requisitos

- Python 3.9 o superior
- PySide6 con Qt WebEngine (incluye su propia copia de Chromium)

```bash
python -m pip install -r requirements.txt
```

**Linux:** si tu distribución gestiona Python con PEP 668, usa
`python3 -m pip install --user --break-system-packages PySide6`. Qt 6 necesita
además `libxcb-cursor.so.0` bajo X11; `instalar.sh` la descarga sola si falta.

## Uso

**Windows**

```bat
pedrozilla\run.bat                            :: abre el navegador
pedrozilla\run.bat example.com wikipedia.org   :: abre direcciones al arrancar
pedrozilla\run.bat "receta de tortilla"        :: abre una búsqueda
pedrozilla\run.bat --incognito                 :: ventana privada
pedrozilla\run.bat --debug                     :: muestra la consola JavaScript
```

**Linux**

```bash
./pedrozilla/run.sh [opciones] [URL ...]
```

En ambos casos también vale `python -m pedrozilla <URL>` desde la carpeta que
contiene al paquete. Arranca con `Ctrl+Shift+I` para las herramientas de
desarrollo.

## Instalarlo en el escritorio

- **Windows** → `pedrozilla\instalar.bat`: icono y accesos directos en el
  Escritorio (normal y privada) y en el menú Inicio.
- **Linux** → `./pedrozilla/instalar.sh`: icono, entrada de menú, acceso directo
  y el comando `pedrozilla`.

Vuelve a ejecutarlo si mueves la carpeta del proyecto.

## Distribuir sin Python

```bat
crear_exe.bat      :: dist\Pedrozilla\Pedrozilla.exe       portátil (carpeta autosuficiente)
crear_setup.bat    :: dist\PedrozillaSetup-1.1.0.exe       instalador de un clic
```

El instalador no pide Python ni administrador: instala en
`%LOCALAPPDATA%\Pedrozilla`, crea los accesos directos y se registra en
*Configuración → Aplicaciones* para poder desinstalarlo.

Vuelve a ejecutar ambos scripts cada vez que cambies el código: el `.exe` lleva
dentro una copia del navegador del momento de compilarlo.

## Estructura

```
pedrozilla/
├── main.py              arranque, argumentos de línea de comandos y perfiles
├── browser.py           ventana: pestañas, barra de direcciones, menús, atajos
├── webview.py           QWebEngineView/QWebEnginePage (motor Chromium)
├── storage.py           ajustes, historial, marcadores y sesión (JSON)
├── downloads.py         descargas: seguimiento, barra y diálogo
├── dialogs.py           historial, marcadores, ajustes y "acerca de"
├── extensions.py        extensiones Chromium (MV3)
├── newtab.py            HTML de la página de nueva pestaña
├── newtab_bridge.py     puente Qt ↔ JavaScript de esa página
├── theme.py             temas clásico, oscuro y claro
├── utils.py             parseo de la barra de direcciones y formateo
├── run.sh / run.bat     lanzadores
└── instalar.sh/.bat/.ps1  accesos directos de escritorio
```

`pedrozilla_launcher.py` es el punto de entrada que usa PyInstaller;
`installer/pedrozilla.nsi` es la receta del instalador de Windows.

## Donde se guardan los datos

**Windows**

- Ajustes, historial y marcadores: `%APPDATA%\pedrozilla\`
- Perfil de Chromium (cookies, caché, almacenamiento web): `%LOCALAPPDATA%\pedrozilla\`
- Descargas: `%USERPROFILE%\Downloads` o la carpeta que elijas en Ajustes

**Linux** (se respetan `XDG_CONFIG_HOME` y `XDG_DATA_HOME`)

- Ajustes, historial y marcadores: `~/.config/pedrozilla/`
- Perfil de Chromium: `~/.local/share/pedrozilla/`
- Descargas: `~/Downloads` o la carpeta que elijas en Ajustes

Todo se borra desde *Ajustes → Avanzado → Borrar datos de navegación* o
borrando esas carpetas.

## Limitaciones conocidas

- Sin sincronización ni cuentas; las extensiones MV3 son propias y no se
  importan los marcadores de Chrome.
- El menú contextual y las páginas internas son propios (no replican `chrome://`).
- Para vídeo con códecs propietarios (H.264) puede hace falta la versión de Qt
  WebEngine del sistema en lugar de la de `pip`.
- Google rechaza el inicio de sesión y el alta de cuentas en navegadores
  incrustados: es un bloqueo de Google, no del motor.

## Licencia

MIT. Puedes usar, modificar y distribuir Pedrozilla libremente; consulta
[LICENSE](LICENSE).
