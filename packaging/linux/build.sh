#!/usr/bin/env bash
# Construye los paquetes Linux: instalador portátil (.tar.gz) y .deb.
#
# Uso:
#   ./packaging/linux/build.sh 1.1.1
#
# Requisitos: python3 con PyInstaller y PySide6, dpkg-deb, tar, gzip.
set -euo pipefail

VERSION="${1:?Uso: build.sh VERSION}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${OUT_DIR:-$ROOT/dist-linux}"
BUILD="${BUILD_DIR:-/tmp/pedrozilla-linux-build}"
PYTHON="${PYTHON:-python3}"

rm -rf "$OUT" "$BUILD"
mkdir -p "$OUT" "$BUILD"

cd "$ROOT"

echo "==> Creando ejecutable autónomo"
"$PYTHON" -m PyInstaller \
  --noconfirm --clean --windowed \
  --name Pedrozilla \
  --icon "$ROOT/pedrozilla/pedrozilla.ico" \
  --add-data "$ROOT/pedrozilla/pedrozilla.ico:pedrozilla" \
  --add-data "$ROOT/pedrozilla/data/qwebchannel.js:pedrozilla/data" \
  --hidden-import pedrozilla.updates \
  --workpath "$BUILD/work" \
  --distpath "$BUILD/dist" \
  --specpath "$BUILD/spec" \
  "$ROOT/pedrozilla_launcher.py"

APP="$BUILD/dist/Pedrozilla"
if [ ! -x "$APP/Pedrozilla" ]; then
  echo "ERROR: PyInstaller no generó $APP/Pedrozilla" >&2
  exit 1
fi

# En CI la librería se instala con apt; en local puede venir del proyecto.
if [ -f "$ROOT/pedrozilla/libs/libxcb-cursor.so.0.0.0" ]; then
  cp "$ROOT/pedrozilla/libs/libxcb-cursor.so.0.0.0" "$APP/_internal/libxcb-cursor.so.0"
fi

QT_QPA_PLATFORM=offscreen "$APP/Pedrozilla" --version

echo "==> Creando paquete portátil"
STAGE="$BUILD/linux"
mkdir -p "$STAGE"
cp -a "$APP" "$STAGE/Pedrozilla"
sed "s/__VERSION__/$VERSION/g" "$ROOT/packaging/linux/install.sh" > "$STAGE/install.sh"
cp "$ROOT/packaging/linux/uninstall.sh" "$STAGE/uninstall.sh"
cp "$ROOT/packaging/linux/pedrozilla.png" "$STAGE/pedrozilla.png"
cp "$ROOT/LICENSE" "$STAGE/LICENSE"
cp "$ROOT/README.md" "$STAGE/README.md"
chmod 755 "$STAGE/install.sh" "$STAGE/uninstall.sh"

cat > "$STAGE/README.txt" <<EOF
Pedrozilla $VERSION para Linux x86_64
=====================================

Este paquete no necesita Python ni permisos de administrador.

Instalar:
  ./install.sh

Abrir:
  pedrozilla
  o busca "Pedrozilla" en el menú de aplicaciones.

Desinstalar:
  ./uninstall.sh

Los datos de navegación se guardan en ~/.local/share/pedrozilla y se conservan
aunque desinstales el programa.

Requisitos: Linux x86_64 con glibc 2.39 o superior (Ubuntu 24.04, Linux Mint
22 o distribuciones equivalentes).
EOF

tar -C "$STAGE" -czf "$OUT/Pedrozilla-${VERSION}-linux-x86_64.tar.gz" .

echo "==> Creando paquete .deb"
DEB="$BUILD/deb"
mkdir -p \
  "$DEB/DEBIAN" \
  "$DEB/opt/pedrozilla" \
  "$DEB/usr/bin" \
  "$DEB/usr/share/applications" \
  "$DEB/usr/share/icons/hicolor/256x256/apps" \
  "$DEB/usr/share/doc/pedrozilla"

cp -a "$APP/." "$DEB/opt/pedrozilla/"
cp "$ROOT/LICENSE" "$DEB/usr/share/doc/pedrozilla/copyright"
cp "$ROOT/README.md" "$DEB/usr/share/doc/pedrozilla/README.md"
cp "$ROOT/packaging/linux/pedrozilla.png" \
  "$DEB/usr/share/icons/hicolor/256x256/apps/pedrozilla.png"

cat > "$DEB/usr/bin/pedrozilla" <<'EOF'
#!/bin/sh
exec /opt/pedrozilla/Pedrozilla "$@"
EOF
chmod 755 "$DEB/usr/bin/pedrozilla"

cat > "$DEB/usr/share/applications/pedrozilla.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=Pedrozilla
GenericName=Navegador web
Comment=Navegador web basado en Chromium (Qt WebEngine)
Exec=/opt/pedrozilla/Pedrozilla %u
Path=/opt/pedrozilla
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
Exec=/opt/pedrozilla/Pedrozilla --incognito
EOF

cat > "$DEB/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
exit 0
EOF

cat > "$DEB/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
exit 0
EOF
chmod 755 "$DEB/DEBIAN/postinst" "$DEB/DEBIAN/postrm"

INSTALLED_SIZE="$(du -sk "$DEB" | awk '{print $1}')"
cat > "$DEB/DEBIAN/control" <<EOF
Package: pedrozilla
Version: $VERSION
Architecture: amd64
Maintainer: ravesh1t <pedro.hostale@gmail.com>
Installed-Size: $INSTALLED_SIZE
Depends: libc6, libx11-6, libxext6, libxrender1, libxcomposite1, libxdamage1, libxrandr2, libxtst6, libxi6, libnss3, libxkbcommon0, libxkbcommon-x11-0, libglib2.0-0t64 | libglib2.0-0, libasound2t64 | libasound2
Section: web
Priority: optional
Homepage: https://github.com/ravesh1t/pedrozilla
Description: Navegador de escritorio basado en Chromium (Qt WebEngine)
 Pedrozilla es un navegador de escritorio con interfaz propia sobre Qt WebEngine.
 Incluye pestañas, historial, marcadores, descargas, modo privado y extensiones.
EOF

dpkg-deb --build --root-owner-group "$DEB" \
  "$OUT/pedrozilla_${VERSION}_amd64.deb"

echo
echo "Listo:"
ls -lh "$OUT"
