#!/usr/bin/env bash
# Migra los datos de Pedrozilla 1.x (motor Chromium/Qt) a Firefox.
#
# Lee ~/.config/pedrozilla/bookmarks.json (lista de {title, url}) y genera
# un HTML en formato Netscape dentro del perfil, listo para importar desde
# Firefox: Biblioteca (Ctrl+Shift+O) > Importar y respaldar > Importar
# marcadores desde HTML.
#
# No modifica ni borra los datos originales.
set -euo pipefail

CONFIG_BASE="${XDG_CONFIG_HOME:-$HOME/.config}"
PROFILE="$CONFIG_BASE/pedrozilla/firefox-profile"
LEGACY="$CONFIG_BASE/pedrozilla/bookmarks.json"

if [ ! -f "$LEGACY" ]; then
  echo "   (sin datos de Pedrozilla 1.x: no hay nada que migrar)"
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "   AVISO: hace falta python3 para convertir los marcadores; se omite."
  exit 0
fi

mkdir -p "$PROFILE"
TARGET="$PROFILE/bookmarks-pedrozilla-1x.html"
python3 - "$LEGACY" "$TARGET" <<'PYTHON'
import html, json, sys
src, target = sys.argv[1], sys.argv[2]
try:
    items = json.load(open(src, encoding="utf-8"))
except Exception as exc:
    print(f"   AVISO: no se pudo leer {src} ({exc}), se omite.")
    sys.exit(0)
if not isinstance(items, list):
    items = []
cards = []
for item in items:
    if not isinstance(item, dict):
        continue
    url = str(item.get("url", ""))
    title = str(item.get("title", "")) or url
    if not url:
        continue
    cards.append(f'    <DT><A HREF="{html.escape(url, quote=True)}">{html.escape(title)}</A>')
page = "\n".join([
    "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
    '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
    "<TITLE>Marcadores de Pedrozilla 1.x</TITLE>",
    "<H1>Marcadores de Pedrozilla 1.x</H1>",
    "<DL><p>",
    *cards,
    "</DL><p>",
])
open(target, "w", encoding="utf-8").write(page + "\n")
print(f"   {len(cards)} marcadores exportados a:")
print(f"   {target}")
PYTHON
echo "   Importalos en Firefox: Ctrl+Shift+O > Importar y respaldar > Importar marcadores desde HTML."
