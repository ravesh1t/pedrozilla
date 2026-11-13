#!/usr/bin/env bash
# Instalador portátil de Pedrozilla para Linux (sin root y sin Python).
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="__VERSION__"
DEST="$HOME/.local/opt/pedrozilla"
BIN_DIR="$HOME/.local/bin"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APPS_DIR="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/256x256/apps"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
[ -n "$DESKTOP_DIR" ] || DESKTOP_DIR="$HOME/Escritorio"

if [ ! -x "$SRC/Pedrozilla/Pedrozilla" ]; then
  echo "ERROR: falta el ejecutable Pedrozilla. Descomprime el paquete completo." >&2
  exit 1
fi

echo "==> Instalando Pedrozilla $VERSION en $DEST"
rm -rf "$DEST"
mkdir -p "$DEST"
cp -a "$SRC/Pedrozilla/." "$DEST/"

mkdir -p "$BIN_DIR" "$APPS_DIR" "$ICON_DIR"
cat > "$BIN_DIR/pedrozilla" <<EOF
#!/bin/sh
exec "$DEST/Pedrozilla" "\$@"
EOF
chmod 755 "$BIN_DIR/pedrozilla"

cp "$SRC/pedrozilla.png" "$ICON_DIR/pedrozilla.png"

cat > "$APPS_DIR/pedrozilla.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Pedrozilla
GenericName=Navegador web
Comment=Navegador web basado en Chromium (Qt WebEngine)
Exec="$DEST/Pedrozilla" %u
Path=$DEST
Icon=pedrozilla
Terminal=false
StartupNotify=true
StartupWMClass=Pedrozilla
Categories=Network;WebBrowser;
Keywords=navegador;browser;web;internet;chromium;
MimeType=text/html;x-scheme-handler/http;x-scheme-handler/https;
Actions=private;

[Desktop Action private]
Name=Abrir una ventana privada
Exec="$DEST/Pedrozilla" --incognito
EOF

if [ -d "$DESKTOP_DIR" ]; then
  cp "$APPS_DIR/pedrozilla.desktop" "$DESKTOP_DIR/Pedrozilla.desktop"
  chmod 755 "$DESKTOP_DIR/Pedrozilla.desktop"
fi

update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
gtk-update-icon-cache -q -t -f "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true

echo
echo "Pedrozilla $VERSION instalado."
echo "  Ejecuta: pedrozilla"
echo "  Menú:    busca \"Pedrozilla\""
echo "  Datos:   $DATA_HOME/pedrozilla (se conservan al desinstalar)"
