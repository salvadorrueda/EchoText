#!/bin/bash

# Script d'instal·lació unificat per a EchoText (Whisper Live)
# Aquest script instal·la les dependències de sistema, configura l'entorn virtual
# i crea un comando global 'echotext'.

# Sortir si hi ha algun error
set -e

INSTALL_DIR=$(pwd)
BIN_DIR="$HOME/.local/bin"

echo "--- [1/5] Iniciant la instal·lació de dependències de sistema ---"
if command -v apt >/dev/null; then
    sudo apt update
    sudo apt install -y python3-pip python3-venv ffmpeg libportaudio2 xclip git
else
    echo "Avís: 'apt' no trobat. Assegura't d'instal·lar 'ffmpeg', 'libportaudio2', 'python3-venv', 'xclip' i 'git' manualment."
fi

echo "--- [2/5] Creant l'entorn virtual (venv) ---"
if [ -d "venv" ]; then
    echo "L'entorn virtual ja existeix. Saltant pas."
else
    python3 -m venv venv
    echo "Entorn virtual creat."
fi

echo "--- [3/5] Instal·lant paquets de Python dins del venv ---"
source venv/bin/activate
pip install --upgrade pip
pip install openai-whisper setuptools-rust sounddevice scipy numpy pyperclip

echo "--- [4/5] Configurant el comando global 'echotext' ---"
mkdir -p "$BIN_DIR"

cat << EOF > "$BIN_DIR/echotext"
#!/bin/bash
source "$INSTALL_DIR/venv/bin/activate"
python3 "$INSTALL_DIR/whisper_live.py" "\$@"
EOF

chmod +x "$BIN_DIR/echotext"

echo "--- [5/5] Configurant el PATH a .bashrc ---"
if ! grep -q "$BIN_DIR" "$HOME/.bashrc"; then
    echo "" >> "$HOME/.bashrc"
    echo "# EchoText path" >> "$HOME/.bashrc"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"
    echo "S'ha afegit $BIN_DIR al PATH a .bashrc"
else
    echo "$BIN_DIR ja està al PATH."
fi

echo ""
echo "--- INSTAL·LACIÓ FINALITZADA AMB ÈXIT ---"
echo ""
echo "Per utilitzar EchoText, reinicia la terminal o executa:"
echo "source ~/.bashrc"
echo ""
echo "Després podràs utilitzar el comando global:"
echo "echotext"
echo ""
echo "O directament des d'aquest directori:"
echo "- python3 whisper_simple.py"
echo "- python3 whisper_live.py"
echo "----------------------------------------"
