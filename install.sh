#!/bin/bash

# --- IMPORTANTE: CAMBIA ESTO POR TU URL DE GITHUB ---
REPO_URL="PON_AQUI_TU_URL_DE_GITHUB" 

INSTALL_DIR="$HOME/.local/share/vibeeq"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "--- Instalando VibeEQ ---"

# 1. Instalar dependencias
if command -v pacman &> /dev/null; then
    sudo pacman -S --noconfirm python-pip tk easyeffects git
elif command -v apt &> /dev/null; then
    sudo apt update && sudo apt install -y python3-tk easyeffects git
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3-tkinter easyeffects git
fi

# 2. Descargar la App
if [ -d "$INSTALL_DIR" ]; then
    echo "Actualizando..."
    cd "$INSTALL_DIR" && git pull
else
    echo "Descargando..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# 3. Crear icono en el menú
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/vibeeq.desktop" <<EOF
[Desktop Entry]
Name=VibeEQ Manager
Exec=python3 $INSTALL_DIR/main.py
Icon=audio-card
Terminal=false
Type=Application
Categories=Audio;
EOF

chmod +x "$DESKTOP_DIR/vibeeq.desktop"

echo "--- ¡Listo! Busca VibeEQ en tu menú ---"
