#!/usr/bin/env bash
# Prepara el perfil Firefox de Pedrozilla sin tocar el perfil normal.
# Uso: init-profile.sh [DIR_PROYECTO]
# Es idempotente: nunca sobrescribe un user.js existente.
set -euo pipefail

PROJECT_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
CONFIG_BASE="${XDG_CONFIG_HOME:-$HOME/.config}"
PROFILE="$CONFIG_BASE/pedrozilla/firefox-profile"
SKELETON="$PROJECT_DIR/firefox-profile-skeleton"
NEWTAB_SRC="$PROJECT_DIR/newtab/index.html"

mkdir -p "$PROFILE/chrome"
NEWTAB_TARGET="$PROFILE/pedrozilla-newtab.html"
cp -f "$NEWTAB_SRC" "$NEWTAB_TARGET"
cp -f "$SKELETON/chrome/userChrome.css" "$PROFILE/chrome/userChrome.css"

if [ ! -f "$PROFILE/user.js" ]; then
  FILE_URL="file://$(echo "$NEWTAB_TARGET" | sed 's/ /%20/g')"
  sed "s|__PEDROZILLA_NEWTAB_URL__|$FILE_URL|" "$SKELETON/user.js" > "$PROFILE/user.js"
  LEGACY="$CONFIG_BASE/pedrozilla/settings.json"
  if [ -f "$LEGACY" ] && command -v python3 >/dev/null 2>&1; then
    ENGINE="$(python3 -c "import json;print(json.load(open('$LEGACY')).get('search_engine',''))" 2>/dev/null || true)"
    case "$ENGINE" in
      google) NAME="Google" ;;
      brave) NAME="Brave" ;;
      bing) NAME="Bing" ;;
      ecosia) NAME="Ecosia" ;;
      wikipedia) NAME="Wikipedia" ;;
      youtube) NAME="YouTube" ;;
      *) NAME="" ;;
    esac
    if [ -n "$NAME" ]; then
      sed -i "s/\"DuckDuckGo\"/\"$NAME\"/g" "$PROFILE/user.js"
    fi
  fi
  echo "perfil creado en $PROFILE"
else
  echo "perfil ya existente en $PROFILE"
fi
echo "$PROFILE"
