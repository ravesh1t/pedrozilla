# Pedrozilla 2.x

Distribución de **Firefox (motor Gecko)** con marca, perfil y tema propios de
Pedrozilla: pestañas arriba, botón naranja de menú, una sola barra de
direcciones (sin caja de búsqueda aparte) y página local de nueva pestaña.

> La versión 1.x (navegador propio en Python + Qt/Chromium) queda archivada en
> `legacy/` como referencia. Desde 2.0 el motor es Firefox de verdad.

```
pedrozilla/                        <- el repositorio
├── README.md
├── VERSION                        versión actual (2.0.0)
├── run.bat / run.sh               lanzadores (Windows / Linux)
├── instalar.bat / instalar.ps1    instalador (Windows)
├── instalar.sh                    instalador (Linux)
├── assets/
│   └── pedrozilla.ico             icono de accesos directos
├── firefox-profile-skeleton/
│   ├── user.js                    preferencias del perfil Pedrozilla
│   └── chrome/
│       └── userChrome.css         retoques estilo Firefox 7
├── newtab/
│   └── index.html                 página local de inicio/nueva pestaña
├── tools/
│   ├── init-profile.ps1/.sh       prepara el perfil (idempotente)
│   └── migrate-1x.ps1/.sh         exporta marcadores de Pedrozilla 1.x a HTML
└── legacy/                        código 1.x archivado (Python + Qt WebEngine)
    ├── pedrozilla-qt/             ...incluye run/instalar/crear_exe originales
    ├── pedrozilla_launcher.py
    ├── crear_exe.bat
    └── requirements.txt
```

## Requisitos

- **Firefox** instalado (se usa su motor Gecko; no se instala otro navegador):
  `https://www.mozilla.org/firefox/`
- Sin Python, sin compilación, sin administrador.

## Instalarlo en el escritorio

**Windows** — doble clic en `instalar.bat` (o `instalar.bat --no-pause` desde
terminal). Prepara el perfil en `%APPDATA%\pedrozilla\firefox-profile`, migra
los marcadores de 1.x si existen y crea accesos directos en el Escritorio
(normal y privada) y en el menú Inicio, con el icono de Pedrozilla.

**Linux** — un solo paso:

```bash
./instalar.sh
```

Prepara el perfil en `~/.config/pedrozilla/firefox-profile` (respeta
`XDG_CONFIG_HOME`), crea la entrada del menú de aplicaciones, el acceso
directo del escritorio y el comando `pedrozilla` en `~/.local/bin`.

## Uso

**Windows:**

```bat
run.bat                                :: abre Pedrozilla
run.bat ejemplo.com wikipedia.org      :: abre direcciones al arrancar
run.bat --incognito                    :: ventana privada
run.bat --version                      :: muestra la versión
```

**Linux:**

```bash
./run.sh                               # abre Pedrozilla
./run.sh ejemplo.com wikipedia.org     # abre direcciones al arrancar
./run.sh --incognito                   # ventana privada
```

En Linux, si Firefox no está en el `PATH` (p. ej. solo Snap/Flatpak con otra
ruta), indica el binario con `PEDROZILLA_FIREFOX=/ruta/a/firefox ./run.sh`.

## Dónde están los datos

Se reutiliza la carpeta de siempre, con una subcarpeta nueva para Firefox:

- **Windows:** `%APPDATA%\pedrozilla\`
  - `firefox-profile\` → perfil Firefox de Pedrozilla (no toca tu perfil normal)
  - `settings.json`, `bookmarks.json`, `history.json` → datos heredados de 1.x
- **Linux:** `~/.config/pedrozilla/` (respeta `XDG_CONFIG_HOME`), igual esquema.

Para volver al aspecto y ajustes de fábrica, borra `firefox-profile\`: se
regenera solo en el siguiente arranque.

## Migración desde Pedrozilla 1.x

El instalador la ejecuta solo:

1. Tu motor de búsqueda de 1.x se conserva en el perfil nuevo (si era Google,
   Brave, Bing, Ecosia, Wikipedia o YouTube; si no, DuckDuckGo).
2. Tus marcadores se exportan a `firefox-profile\bookmarks-pedrozilla-1x.html`.
   Impórtalos en Firefox con `Ctrl+Shift+O` → *Importar y respaldar* →
   *Importar marcadores desde HTML*.
3. Los datos originales de 1.x no se tocan.

## Notas

- Todo funciona sin permisos de administrador porque la configuración vive en
  el **perfil**, no en la carpeta de instalación de Firefox (a propósito no se
  usa `policies.json` global).
- El `userChrome.css` imita el Firefox 7 dentro de lo que permite el Firefox
  actual; si alguna regla no coincide con tu versión, se ignora sin romper nada.
- Sin sincronización ni extensiones preinstaladas: es Firefox con valores y
  marca de Pedrozilla.

## Licencia

MIT. Puedes usar, modificar y distribuir Pedrozilla libremente; consulta el
archivo [LICENSE](LICENSE).
