# Pedrozilla

> **1.1.2** — navegador de escritorio basado en Chromium (Qt WebEngine).

Slop pura y dura que come RAM todo el día: Chromium metido en Python (PySide6),
con interfaz moderna y personalizable. Incluye los temas **Moderno**
(predeterminado en nuevas instalaciones), Clásico tipo Firefox 7, Oscuro y
Claro. Sin cuentas ni sincronización.

Esta revisión añade la nueva pestaña de tablero (notas, recordatorios y enlaces),
grupos de pestañas, espacios de trabajo, vista dividida, modo lectura, centro de
privacidad y un diálogo de ajustes con barra lateral y buscador, sin cambiar el
motor ni la versión del navegador. La barra de menús clásica ya no se muestra: la barra de
pestañas es lo primero que aparece y todas sus acciones están en el menú del
botón naranja, organizado en ARCHIVO, EDITAR, VER, HISTORIAL, MARCADORES,
DESCARGAS, HERRAMIENTAS y AYUDA, con iconos SVG en línea, atajos a la derecha y
un fundido sutil al abrirse. Los atajos siguen funcionando igual.

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

## Funciones nuevas

- **Nueva pestaña (tablero):** reloj, fecha, saludo y buscador sobre un fondo de
  paisaje, con tarjetas de NOTAS, RECORDATORIOS, BUILD y DAILY. Permite añadir,
  marcar y eliminar elementos, crear secciones propias, deshacer/rehacer y
  filtrar enlaces. Los accesos y páginas recientes del perfil se usan como
  contenido inicial; los cambios se guardan en `settings.json` mediante
  QWebChannel. El buscador usa el motor configurado y navega en la misma
  pestaña. Los espacios de trabajo se muestran arriba y se cambian desde el
  menú naranja.
- **Pestañas:** fijar, silenciar, agrupar por colores, contraer grupos, dividir
  la pestaña en dos vistas independientes y recuperar pestañas cerradas desde
  el historial.
- **Espacios de trabajo:** cada espacio conserva sus pestañas, grupos y color.
  Se cambia desde el menú *Espacios* o con `Alt+W`.
- **Modo lectura (`F9`):** extrae el contenido principal de la página con
  heurísticas locales, sin servicios externos. `Esc` lo cierra.
- **Centro de privacidad:** permisos del sitio, control de JavaScript, cookies,
  caché y certificados, usando las APIs reales de Qt WebEngine.
- **Ajustes rediseñados:** 11 categorías en barra lateral, buscador y
  restauración de valores por defecto.

### Atajos añadidos

| Atajo | Acción |
| --- | --- |
| `F9` | Modo lectura |
| `Alt+V` | Dividir / unir la vista |
| `Alt+P` | Fijar o desfijar la pestaña |
| `Alt+M` | Silenciar la pestaña |
| `Alt+G` | Crear grupo de pestañas |
| `Alt+Shift+G` | Gestionar grupos |
| `Alt+W` | Cambiar de espacio de trabajo |
| `Ctrl+L` / `Alt+D` | Ir a la barra de direcciones |

## Instalarlo en el escritorio

- **Windows** → `pedrozilla\instalar.bat`: icono y accesos directos en el
  Escritorio (normal y privada) y en el menú Inicio.
- **Linux** → `./pedrozilla/instalar.sh`: icono, entrada de menú, acceso directo
  y el comando `pedrozilla`.

Vuelve a ejecutarlo si mueves la carpeta del proyecto.

## Distribuir sin Python

```bat
crear_exe.bat      :: dist\Pedrozilla\Pedrozilla.exe       portátil (carpeta autosuficiente)
crear_setup.bat    :: dist\PedrozillaSetup-1.1.2.exe       instalador de un clic
```

El instalador no pide Python ni administrador: instala en
`%LOCALAPPDATA%\Pedrozilla`, crea los accesos directos y se registra en
*Configuración → Aplicaciones* para poder desinstalarlo.

Vuelve a ejecutar ambos scripts cada vez que cambies el código: el `.exe` lleva
dentro una copia del navegador del momento de compilarlo.

**Linux** (paquete portátil y `.deb` autosuficientes):

```bash
./packaging/linux/build.sh 1.1.2
# dist-linux/Pedrozilla-1.1.2-linux-x86_64.tar.gz
# dist-linux/pedrozilla_1.1.2_amd64.deb
```

El `.tar.gz` se instala sin root con `./install.sh`; el `.deb` instala en
`/opt/pedrozilla`. Ambos incluyen Qt WebEngine, así que no necesitan Python.

## Actualizaciones

Pedrozilla consulta una vez al día la última release publicada en
[GitHub](https://github.com/ravesh1t/pedrozilla/releases) y avisa si hay una
versión nueva. No envía telemetría ni descarga nada por su cuenta. También
puedes comprobarlo a mano en el menú naranja de Pedrozilla → *AYUDA → Buscar
actualizaciones* o desactivar la comprobación automática en *Ajustes → General*.

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
├── updates.py           comprobación de releases en GitHub
├── newtab.py            datos inyectados en la página de nueva pestaña
├── newtab_template.py   HTML del tablero (diseño adjuntado)
├── newtab_bridge.py     puente Qt ↔ JavaScript de esa página
├── icons.py             iconos SVG en línea del menú principal
├── reader.py            modo lectura y solicitud de PiP nativo
├── theme.py             temas moderno, clásico, oscuro y claro
├── utils.py             parseo de la barra de direcciones y formateo
├── run.sh / run.bat     lanzadores
└── instalar.sh/.bat/.ps1  accesos directos de escritorio
tests/
└── test_pedrozilla.py   pruebas unittest (nueva pestaña, GUI, ajustes, grupos…)
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

Todo se borra desde *Ajustes → Privacidad y seguridad → Borrar datos de
navegación* (o *Historial → Borrar datos de navegación*) o borrando esas
carpetas. La política de referrer se aplica mediante una etiqueta `<meta>`
local; Qt WebEngine no expone la cabecera HTTP ni Do Not Track.

## Pruebas

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v
```

No instalan dependencias nuevas ni escriben en tu perfil real: usan un
directorio temporal.

## Limitaciones conocidas

- Sin sincronización ni cuentas; las extensiones MV3 son propias y no se
  importan los marcadores de Chrome.
- **Picture in Picture:** Qt WebEngine no ofrece una API para controlar la
  ventana flotante de Chromium. Pedrozilla solo puede pedir el PiP nativo desde
  la página (`requestPictureInPicture`); no puede moverlo ni redimensionarlo.
- **Favicons:** Qt WebEngine no expone una API para leer su base de favicons,
  así que las iniciales con color se mantienen como icono de respaldo.
- **Almacenamiento local:** no existe una API de Qt para enumerar `localStorage`
  de todos los orígenes. Borrar datos limpia el de las pestañas abiertas y el
  directorio `Local Storage` del perfil; puede ser necesario recargar.
- **Sesión:** el archivo de sesión describe una sola ventana (la última normal
  que queda abierta). Los espacios de trabajo se guardan aparte en los ajustes.
- **Modo lectura:** es heurístico. Si la página no tiene suficiente texto
  identificable, se informa y la página queda intacta.
- **Menú desplegable:** el QSS de Qt no admite `box-shadow` ni una animación
  fiable de cierre en menús modales; el tema Modern usa borde y esquinas
  redondeadas para dar profundidad y un fundido sutil al abrir.
- El menú contextual y las páginas internas son propios (no replican `chrome://`).
- Para vídeo con códecs propietarios (H.264) puede hace falta la versión de Qt
  WebEngine del sistema en lugar de la de `pip`.
- Google rechaza el inicio de sesión y el alta de cuentas en navegadores
  incrustados: es un bloqueo de Google, no del motor.

## Licencia

MIT. Puedes usar, modificar y distribuir Pedrozilla libremente; consulta
[LICENSE](LICENSE).
