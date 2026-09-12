#!/usr/bin/env bash
#
# Construye un paquete .deb instalable con apt/dpkg para Guxing.
#
# Uso (ejecutar una sola vez, desde la raíz del proyecto, para generar el
# paquete que luego se distribuye/instala):
#
#   chmod +x build-deb.sh
#   ./build-deb.sh
#   sudo apt install ./guxing_1.0.0_all.deb
#
# Para desinstalar por completo (borra también ~/.config/guxing de todos
# los usuarios y el .desktop/icono, gestionado automáticamente por dpkg):
#
#   sudo apt remove guxing
#   # o, para asegurarte de que se limpia todo:
#   sudo apt purge guxing
#
set -euo pipefail

PKG_NAME="guxing"
VERSION="1.0.0"
ARCH="all"
MAINTAINER="Guxing <guxing@example.com>"

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$SRC_DIR/build/${PKG_NAME}_${VERSION}_${ARCH}"
DEB_FILE="$SRC_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "ERROR: dpkg-deb no está disponible. Instala 'dpkg-dev' (sudo apt install dpkg-dev)." >&2
    exit 1
fi

echo "==> Preparando estructura del paquete en: $PKG_DIR"
rm -rf "$PKG_DIR" "$DEB_FILE"
ICON_SIZES=(16 24 32 48 64 128 256 512)

mkdir -p \
    "$PKG_DIR/DEBIAN" \
    "$PKG_DIR/opt/guxing" \
    "$PKG_DIR/usr/share/applications" \
    "$PKG_DIR/usr/bin"
for size in "${ICON_SIZES[@]}"; do
    mkdir -p "$PKG_DIR/usr/share/icons/hicolor/${size}x${size}/apps"
done

# 1. Código de la aplicación -> /opt/guxing
#    (se excluye todo lo que es solo para desarrollo/otros instaladores)
rsync -a \
    --exclude ".venv" \
    --exclude "__pycache__" \
    --exclude "*.pyc" \
    --exclude ".git" \
    --exclude "config.json" \
    --exclude "*_Bilingue.html" \
    --exclude "launcher.py" \
    --exclude "install.sh" \
    --exclude "uninstall.sh" \
    --exclude "build-deb.sh" \
    --exclude "build" \
    --exclude "Iniciar_Traductor.bat" \
    --exclude "*.deb" \
    "$SRC_DIR"/ "$PKG_DIR/opt/guxing/"

# 2. Icono -> tema de iconos del sistema
#    El PNG original no es cuadrado, así que si se copia tal cual, el tema de
#    iconos lo estira para encajarlo en un cuadro cuadrado y sale "achatado".
#    Para evitarlo, se genera una versión cuadrada con relleno transparente
#    (letterboxing) que conserva las proporciones reales del dibujo, y se
#    exporta en los tamaños estándar que usan los distintos entornos de
#    escritorio (menú, dock, barra de tareas, etc.). Esto requiere
#    ImageMagick ('convert'), que se instala solo si hace falta.
if ! command -v convert >/dev/null 2>&1; then
    echo "==> ImageMagick no encontrado, instalando automáticamente (necesita sudo)..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y imagemagick
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y ImageMagick
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm imagemagick
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y ImageMagick
    else
        echo "AVISO: no se reconoce el gestor de paquetes del sistema." >&2
        echo "       Instala ImageMagick manualmente y vuelve a ejecutar este script." >&2
    fi
fi

ICON_SRC="$SRC_DIR/img/guxing-ico.png"
if [ -f "$ICON_SRC" ]; then
    if command -v convert >/dev/null 2>&1; then
        for size in "${ICON_SIZES[@]}"; do
            convert "$ICON_SRC" \
                -background none \
                -resize "${size}x${size}" \
                -gravity center \
                -extent "${size}x${size}" \
                "$PKG_DIR/usr/share/icons/hicolor/${size}x${size}/apps/guxing.png"
        done
    else
        echo "AVISO: no se pudo instalar ImageMagick automáticamente." >&2
        echo "       El icono se copiará sin corregir su proporción y puede verse deformado." >&2
        echo "       Instálalo manualmente y vuelve a ejecutar build-deb.sh." >&2
        cp "$ICON_SRC" "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/guxing.png"
    fi
else
    echo "AVISO: no se encontró img/guxing-ico.png" >&2
fi

# 3. Lanzador de escritorio (.desktop) -> menú de aplicaciones / barra de tareas
cat > "$PKG_DIR/usr/share/applications/guxing.desktop" <<EOF
[Desktop Entry]
Name=Guxing
Comment=Traductor y lector bilingüe de apuntes
Exec=/opt/guxing/.venv/bin/python /opt/guxing/app.py
Icon=guxing
Terminal=false
Type=Application
Categories=Utility;Office;Education;
StartupWMClass=guxing
EOF

# 4. Comando "guxing" en el PATH del sistema
cat > "$PKG_DIR/usr/bin/guxing" <<'EOF'
#!/usr/bin/env bash
exec /opt/guxing/.venv/bin/python /opt/guxing/app.py "$@"
EOF
chmod 755 "$PKG_DIR/usr/bin/guxing"

# 5. Metadatos del paquete Debian
cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: $PKG_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: python3, python3-venv, python3-pip, python3-tk
Maintainer: $MAINTAINER
Description: Plataforma de traducción, alineación y lectura bilingüe de documentos
 Guxing procesa documentos PDF, DOCX, ODT y TXT, los traduce con motores
 de IA (Gemini, DeepSeek, OpenAI) reteniendo terminología técnica, y
 genera un lector interactivo HTML bilingüe con sincronización de lectura.
EOF

# 6. postinst: se ejecuta tras instalar los archivos -> crea el venv y las deps
cat > "$PKG_DIR/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e

APP_DIR="/opt/guxing"

echo "Guxing: preparando el entorno de Python (puede tardar un minuto)..."
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/.venv/bin/pip" install --quiet \
    openai pymupdf pypdf python-docx odfpy pillow tkinterdnd2

# Permisos de lectura/ejecución para todos los usuarios del sistema
chmod -R a+rX "$APP_DIR"

command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true

exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# 7. prerm: se ejecuta antes de quitar los archivos -> borra el venv generado
#    (el venv no lo gestiona dpkg porque se creó en postinst, no es parte del
#    paquete, así que hay que limpiarlo a mano o quedaría huérfano en disco)
cat > "$PKG_DIR/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
rm -rf /opt/guxing/.venv
rm -rf /opt/guxing/__pycache__
exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# 8. postrm: se ejecuta después de quitar los archivos -> limpia lo que dpkg
#    no puede saber que existe: la configuración por usuario en ~/.config y
#    cualquier resto de /opt/guxing. Se ejecuta tanto en remove como en purge
#    para garantizar que no queda nada tras desinstalar.
cat > "$PKG_DIR/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e

case "$1" in
    remove|purge)
        # Restos de /opt/guxing (venv, cachés, etc. no gestionados por dpkg)
        rm -rf /opt/guxing

        # Configuración y API keys guardadas por CADA usuario del sistema
        for home_dir in /root /home/*; do
            if [ -d "$home_dir/.config/guxing" ]; then
                rm -rf "$home_dir/.config/guxing"
            fi
        done
        ;;
esac

command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true

exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/postrm"

# 9. Construir el .deb
echo "==> Construyendo el paquete..."
dpkg-deb --build --root-owner-group "$PKG_DIR" "$DEB_FILE"

echo ""
echo "✔ Paquete generado: $DEB_FILE"
echo ""
echo "Instálalo con:"
echo "  sudo apt install \"$DEB_FILE\""
echo ""
echo "Desinstálalo con:"
echo "  sudo apt remove guxing     # o: sudo apt purge guxing"