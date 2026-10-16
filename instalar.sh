#!/usr/bin/env bash
# Instala Pedrozilla 2.x en tu entorno de escritorio (distribucion Firefox):
#   - prepara el perfil propio (~/.config/pedrozilla/firefox-profile)
#   - migra los marcadores de Pedrozilla 1.x a un HTML importable (si existen)
#   - entrada en el menu de aplicaciones, acceso directo en el escritorio,
#     comando "pedrozilla" en ~/.local/bin e iconos si se pueden generar
#
# No necesita administrador. Requiere Firefox instalado.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$PROJECT_DIR/run.sh"
APP_ID="pedrozilla"
DISPLAY_NAME="Pedrozilla"

echo "==> Comprobando Firefox"
if [ -n "${PEDROZILLA_FIREFOX:-}" ]; then
  FF="$PEDROZILLA_FIREFOX"
elif command -v firefox >/dev/null 2>&1; then
  FF="firefox"
elif [ -x /usr/bin/firefox ]; then
  FF="/usr/bin/firefox"
elif [ -x /snap/bin/firefox ]; then
  FF="/snap/bin/firefox"
else
  echo "ERROR: no se encontro Firefox. Instalalo desde:"
  echo "  https://www.mozilla.org/firefox/"
  exit 1
fi
echo "   $FF"
chmod +x "$LAUNCHER"

echo "==> Preparando perfil"
PROFILE="$("$PROJECT_DIR/tools/init-profile.sh" "$PROJECT_DIR" | tail -n 1)"

echo "==> Migrando marcadores de Pedrozilla 1.x (si existen)"
"$PROJECT_DIR/tools/migrate-1x.sh" || true

echo "==> Generando iconos (si hay Python con Pillow)"
ICON_BASE="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"
if python3 -c "import PIL" 2>/dev/null && [ -f "$PROJECT_DIR/assets/pedrozilla.ico" ]; then
  python3 - "$PROJECT_DIR/assets/pedrozilla.ico" "$ICON_BASE" <<'PYTHON'
import sys
from PIL import Image
src, base = sys.argv[1], sys.argv[2]
img = Image.open(src)
import os
for size in (32, 48, 64, 128, 256):
    folder = os.path.join(base, f"{size}x{size}", "apps")
    os.makedirs(folder, exist_ok=True)
    img.resize((size, size)).save(os.path.join(folder, "pedrozilla.png"))
print("   iconos instalados")
PYTHON
else
  echo "   (omitido: se usara el icono generico de Firefox)"
  ICON_FALLBACK="firefox"
fi

APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
[ -d "$DESKTOP_DIR" ] || DESKTOP_DIR="$HOME/Escritorio"
ICON_LINE="Icon=$APP_ID"
[ -n "${ICON_FALLBACK:-}" ] && ICON_LINE="Icon=$ICON_FALLBACK"

echo "==> Creando entrada de menu"
mkdir -p "$APPS_DIR"
write_desktop() {
  cat > "$1" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$DISPLAY_NAME
GenericName=Navegador web
Comment=Navegador web basado en Firefox (Gecko)
Exec="$LAUNCHER" %u
Path=$PROJECT_DIR
$ICON_LINE
Terminal=false
StartupNotify=true
StartupWMClass=$DISPLAY_NAME
Categories=Network;WebBrowser;
Keywords=navegador;browser;web;internet;firefox;gecko;
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

  1. Menu de aplicaciones  ->  escribe "Pedrozilla" (categoria Internet)
  2. Doble clic en el escritorio  ->  $DESKTOP_DIR/$DISPLAY_NAME.desktop
  3. Terminal  ->  pedrozilla        (o "$LAUNCHER")

Proyecto: $PROJECT_DIR
EOF
