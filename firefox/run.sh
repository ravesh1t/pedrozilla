#!/usr/bin/env bash
# Lanzador de Pedrozilla 2.x para Linux (distribucion basada en Firefox).
# Usa un perfil propio (~/.config/pedrozilla/firefox-profile) para no tocar
# el perfil normal de Firefox. No necesita Python ni administrador.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="desconocida"
[ -f "$DIR/VERSION" ] && VERSION="$(cat "$DIR/VERSION")"

for arg in "$@"; do
  if [ "$arg" = "--version" ]; then
    echo "Pedrozilla $VERSION"
    exit 0
  fi
done

find_firefox() {
  if [ -n "${PEDROZILLA_FIREFOX:-}" ] && command -v "$PEDROZILLA_FIREFOX" >/dev/null 2>&1; then
    command -v "$PEDROZILLA_FIREFOX"
    return 0
  fi
  for cmd in firefox /usr/bin/firefox /snap/bin/firefox; do
    if command -v "$cmd" >/dev/null 2>&1; then
      command -v "$cmd"
      return 0
    fi
  done
  return 1
}

FF="$(find_firefox || true)"
if [ -z "$FF" ]; then
  echo "Falta Firefox. Instalalo desde https://www.mozilla.org/firefox/ y vuelve a intentarlo." >&2
  exit 1
fi

# Perfil propio (respeta XDG_CONFIG_HOME como la version 1.x).
PROFILE="$("$DIR/tools/init-profile.sh" "$DIR" | tail -n 1)"

PRIVATE=0
URLS=()
for arg in "$@"; do
  case "$arg" in
    --incognito|-i) PRIVATE=1 ;;
    *) URLS+=("$arg") ;;
  esac
done

if [ "$PRIVATE" = 1 ]; then
  exec "$FF" -profile "$PROFILE" -private-window "${URLS[@]}"
else
  exec "$FF" -profile "$PROFILE" "${URLS[@]}"
fi
