#!/usr/bin/env bash
# Instala Pedrozilla en tu entorno de escritorio:
#   - icono en el tema de iconos del usuario
#   - entrada en el menú de aplicaciones
#   - acceso directo en el escritorio
#   - comando "pedrozilla" en ~/.local/bin
#
# Vuelve a ejecutarlo cada vez que muevas la carpeta del proyecto.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$PROJECT_DIR/run.sh"
APP_ID="pedrozilla"
DISPLAY_NAME="Pedrozilla"
PY="python3"

ICON_BASE="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
[ -d "$DESKTOP_DIR" ] || DESKTOP_DIR="$HOME/Escritorio"

echo "==> Comprobando dependencias"
if ! "$PY" -c "import PySide6.QtWebEngineWidgets" 2>/dev/null; then
  echo "ERROR: falta PySide6 con Qt WebEngine. Instálalo con:"
  echo "  $PY -m pip install --user PySide6"
  exit 1
fi
chmod +x "$LAUNCHER"

# Qt 6 necesita libxcb-cursor.so.0 para el plugin de X11. Si el sistema no la
# trae (habitual en Ubuntu 24.04), dejamos una copia dentro del proyecto: así el
# navegador funciona sin permisos de administrador y sin tocar el sistema.
ensure_xcb_cursor() {
  local libs="$PROJECT_DIR/pedrozilla/libs"
  if ldconfig -p 2>/dev/null | grep -q 'libxcb-cursor\.so\.0'; then
    echo "==> libxcb-cursor disponible en el sistema"
    return 0
  fi
  if [ -f "$libs/libxcb-cursor.so.0" ]; then
    echo "==> Usando la copia local de libxcb-cursor"
    return 0
  fi
  echo "==> libxcb-cursor.so.0 no está en el sistema; descargando copia local"
  local tmp
  tmp="$(mktemp -d)"
  ( cd "$tmp" && apt-get download libxcb-cursor0 >/dev/null 2>&1 ) || true
  local deb
  deb="$(ls "$tmp"/libxcb-cursor0_*.deb 2>/dev/null | head -1 || true)"
  if [ -n "$deb" ]; then
    dpkg-deb -x "$deb" "$tmp/x"
    mkdir -p "$libs"
    cp "$tmp/x/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0.0.0" "$libs/"
    ln -sf libxcb-cursor.so.0.0.0 "$libs/libxcb-cursor.so.0"
    echo "   copia local instalada en $libs"
  else
    echo "   AVISO: no se pudo descargar la librería."
    echo "   Si el navegador no arranca, instala el paquete libxcb-cursor0."
  fi
  rm -rf "$tmp"
}
ensure_xcb_cursor

echo "==> Generando icono"
export PEDROZILLA_PROJECT_DIR="$PROJECT_DIR"
QT_QPA_PLATFORM=offscreen "$PY" - "$ICON_BASE" <<'PYTHON'
import os, sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication

QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
app = QApplication(["pedrozilla-icon"])

sys.path.insert(0, os.environ["PEDROZILLA_PROJECT_DIR"])
from pedrozilla.browser import brand_icon

base = sys.argv[1]
icon = brand_icon(512)
for size in (32, 48, 64, 128, 256):
    folder = os.path.join(base, f"{size}x{size}", "apps")
    os.makedirs(folder, exist_ok=True)
    icon.pixmap(size, size).save(os.path.join(folder, "pedrozilla.png"))
print("   iconos instalados en", base)
PYTHON

echo "==> Creando entrada de menú"
mkdir -p "$APPS_DIR"
write_desktop() {
  cat > "$1" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$DISPLAY_NAME
GenericName=Navegador web
Comment=Navegador web basado en Chromium (Qt WebEngine)
Exec="$LAUNCHER" %u
Path=$PROJECT_DIR
Icon=$APP_ID
Terminal=false
StartupNotify=true
StartupWMClass=$DISPLAY_NAME
Categories=Network;WebBrowser;
Keywords=navegador;browser;web;internet;chromium;
MimeType=text/html;x-scheme-handler/http;x-scheme-handler/https;
Actions=private;

[Desktop Action private]
Name=Abrir una ventana privada
Exec="$LAUNCHER" --incognito
EOF
}

write_desktop "$APPS_DIR/$APP_ID.desktop"
chmod +x "$APPS_DIR/$APP_ID.desktop"

echo "==> Creando comando 'pedrozilla'"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/pedrozilla" <<EOF
#!/usr/bin/env bash
exec "$LAUNCHER" "\$@"
EOF
chmod +x "$BIN_DIR/pedrozilla"

if [ -d "$DESKTOP_DIR" ]; then
  echo "==> Copiando acceso directo a $DESKTOP_DIR"
  write_desktop "$DESKTOP_DIR/$DISPLAY_NAME.desktop"
  chmod +x "$DESKTOP_DIR/$DISPLAY_NAME.desktop"
  if command -v gio >/dev/null 2>&1; then
    gio set "$DESKTOP_DIR/$DISPLAY_NAME.desktop" metadata::trusted true 2>/dev/null || true
  fi
fi

command -v update-desktop-database >/dev/null 2>&1 && \
  update-desktop-database "$APPS_DIR" 2>/dev/null || true

cat <<EOF

Listo. Tres formas de abrirlo:

  1. Menú de aplicaciones  ->  escribe "Pedrozilla" (categoría Internet)
  2. Doble clic en el escritorio  ->  $DESKTOP_DIR/$DISPLAY_NAME.desktop
  3. Terminal  ->  pedrozilla        (o "$LAUNCHER")

Proyecto: $PROJECT_DIR
EOF
