# Pedrozilla

Navegador de escritorio con interfaz propia construido sobre **Chromium** mediante
**Qt WebEngine** (PySide6). No es un envoltorio de otro navegador ni usa servicios
externos: el motor de renderizado es Chromium, el mismo de Google Chrome.

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

## Funciones

**Navegación**
- Barra de direcciones que distingue direcciones de búsquedas (omnibox) con sugerencias
  basadas en historial y marcadores.
- Pestañas: crear, cerrar (botón o clic central), mover, duplicar, cerrar las demás,
  reabrir la última cerrada (`Ctrl+Shift+T`), ciclar con `Ctrl+Tab`.
- Atrás/adelante, recargar, recargar sin caché, detener, inicio, barra de progreso.
- `target="_blank"` y `window.open` abren pestañas nuevas; `window.close()` las cierra.
- Zoom por pestaña y zoom predeterminado configurable.
- Pantalla completa (`F11`) y soporte de pantalla completa de HTML5 (vídeo).
- Buscar en la página (`Ctrl+F`) con contador de coincidencias.
- Páginas internas: `chrome://settings`, `chrome://history`, `chrome://downloads`,
  `chrome://bookmarks`, `chrome://newtab`, `chrome://devtools`.

**Datos**
- Historial con búsqueda, borrado por entrada o completo, y autocompletado.
- Marcadores: estrella, barra de marcadores, renombrar y gestionar.
- Descargas: elegir carpeta, evitar sobrescrituras, barra inferior con progreso,
  pausar/reanudar/cancelar, abrir archivo o carpeta, y diálogo con todas las descargas.
- Ventanas privadas reales (perfil *off-the-record* de Chromium: sin historial, cookies
  ni caché).
- Restauración de sesión opcional y memoria del tamaño de la ventana.
- Guardar página, guardar como PDF e imprimir.
- Cookies persistentes y compartición de sesión entre ejecuciones.

**Seguridad**
- Se rechazan los certificados no verificables (con aviso) salvo que se habilite
  explícitamente en Ajustes → Avanzado.
- Los permisos de cámara, micrófono, ubicación, notificaciones, etc. siempre se
  preguntan al usuario.
- `javascript:` y `data:` escritos en la barra de direcciones se tratan como búsqueda.
- Diálogo de autenticación HTTP básica.

**Interfaz**
- Tema oscuro y claro; menú de aplicación, menú contextual completo (enlaces, imágenes,
  medios, texto seleccionado) y herramientas de desarrollo (`Ctrl+Shift+I`).

## Atajos de teclado

| Atajo | Acción |
| --- | --- |
| `Ctrl+T` / `Ctrl+W` | Nueva pestaña / cerrar pestaña |
| `Ctrl+N` / `Ctrl+Shift+N` | Nueva ventana / ventana privada |
| `Ctrl+Shift+T` | Reabrir la última pestaña cerrada |
| `Ctrl+L` / `Alt+D` | Ir a la barra de direcciones |
| `Ctrl+D` | Guardar o quitar marcador |
| `Ctrl+Shift+B` | Mostrar u ocultar la barra de marcadores |
| `Ctrl+H` / `Ctrl+J` | Historial / descargas |
| `Ctrl+R` / `Ctrl+Shift+R` / `F5` | Recargar / recargar sin caché |
| `Alt+←` / `Alt+→` | Atrás / adelante |
| `Ctrl+F` | Buscar en la página |
| `Ctrl++` / `Ctrl+-` / `Ctrl+0` | Zoom |
| `Ctrl+Shift+I` | Herramientas de desarrollo |
| `Ctrl+S` / `Ctrl+Shift+P` | Guardar página / imprimir o PDF |
| `Ctrl+O` / `Ctrl+U` | Abrir archivo local / ver código fuente |
| `F11` / `F1` | Pantalla completa / acerca de |
| `Ctrl+Tab` / `Ctrl+1…8` | Cambiar de pestaña |

## Dónde se guardan los datos

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
