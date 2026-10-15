#!/usr/bin/env bash
# Lanzador de Pedrozilla.
set -euo pipefail

# Este script vive dentro del paquete pedrozilla/; el módulo se importa
# desde la carpeta que lo contiene.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

# Qt 6 necesita libxcb-cursor.so.0 para el plugin de X11. Si el sistema no la
# tiene instalada, usamos la copia incluida en el proyecto (no requiere root).
if [ -d "$DIR/pedrozilla/libs" ] && ! ldconfig -p 2>/dev/null | grep -q 'libxcb-cursor\.so\.0'; then
  export LD_LIBRARY_PATH="$DIR/pedrozilla/libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

# Chromium acelera por GPU usando DRI3. En máquinas virtuales que solo ofrecen
# DRI2 el contexto gráfico falla y ensucia el registro, así que en ese caso
# (y solo si el usuario no ha indicado lo contrario) forzamos rasterizado por
# software. En un equipo con DRI3 se deja la aceleración activada.
if [ -z "${QTWEBENGINE_CHROMIUM_FLAGS:-}" ] && command -v xdpyinfo >/dev/null 2>&1; then
  if ! xdpyinfo 2>/dev/null | grep -q 'DRI3'; then
    export QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-gpu-compositing"
  fi
fi

if ! python3 -c "import PySide6.QtWebEngineWidgets" 2>/dev/null; then
  echo "Falta PySide6 con Qt WebEngine. Instálalo con:"
  echo "  python3 -m pip install --user PySide6"
  exit 1
fi

exec python3 -m pedrozilla "$@"
