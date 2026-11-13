#!/usr/bin/env bash
# Desinstala la copia portátil de Pedrozilla instalada con install.sh.
set -euo pipefail

DEST="$HOME/.local/opt/pedrozilla"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APPS_DIR="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/256x256/apps"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
[ -n "$DESKTOP_DIR" ] || DESKTOP_DIR="$HOME/Escritorio"

rm -rf "$DEST"
rm -f "$HOME/.local/bin/pedrozilla"
rm -f "$APPS_DIR/pedrozilla.desktop"
rm -f "$ICON_DIR/pedrozilla.png"
rm -f "$DESKTOP_DIR/Pedrozilla.desktop"

update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
gtk-update-icon-cache -q -t -f "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true

echo "Pedrozilla desinstalado. Tus datos de navegación se conservan en:"
echo "  $DATA_HOME/pedrozilla"
