#!/bin/bash

# Script d'instal·lació d'echotextcommand
# Descarrega client_command.py de GitHub i crea ~/.local/bin/echotextcommand

set -e

GITHUB_RAW="https://raw.githubusercontent.com/salvadorrueda/EchoText/main"
INSTALL_DIR="$HOME/.local/share/echotext-command"
BIN_DIR="$HOME/.local/bin"

echo "--- [1/5] Instal·lant dependències de sistema ---"
if command -v apt >/dev/null 2>&1; then
    sudo apt update -q
    sudo apt install -y python3-pip python3-venv libportaudio2 xclip curl
else
    echo "Avís: 'apt' no trobat. Assegura't d'instal·lar 'libportaudio2', 'python3-venv', 'xclip' i 'curl' manualment."
fi

echo "--- [2/5] Creant el directori d'instal·lació: $INSTALL_DIR ---"
mkdir -p "$INSTALL_DIR/lib"
mkdir -p "$BIN_DIR"

echo "--- [3/5] Descarregant fitxers del repositori de GitHub ---"
curl -fsSL "$GITHUB_RAW/client_command.py"      -o "$INSTALL_DIR/client_command.py"
curl -fsSL "$GITHUB_RAW/lib/__init__.py"         -o "$INSTALL_DIR/lib/__init__.py"
curl -fsSL "$GITHUB_RAW/lib/venv_activator.py"  -o "$INSTALL_DIR/lib/venv_activator.py"
curl -fsSL "$GITHUB_RAW/lib/voice_commands.py"  -o "$INSTALL_DIR/lib/voice_commands.py"
echo "Fitxers descarregats correctament."

echo "--- [4/5] Creant l'entorn virtual i instal·lant dependències Python ---"
if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
    echo "Entorn virtual creat."
else
    echo "L'entorn virtual ja existeix. Saltant creació."
fi

"$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/venv/bin/pip" install requests sounddevice numpy scipy pyperclip -q
echo "Dependències Python instal·lades."

echo "--- [5/5] Creant el comando 'echotextcommand' a $BIN_DIR ---"
cat > "$BIN_DIR/echotextcommand" << WRAPPER
#!/bin/bash
exec "$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/client_command.py" "\$@"
WRAPPER
chmod +x "$BIN_DIR/echotextcommand"

# Afegir ~/.local/bin al PATH si no hi és ja
if ! grep -qF '$HOME/.local/bin' "$HOME/.bashrc" 2>/dev/null && \
   ! grep -qF "$HOME/.local/bin" "$HOME/.bashrc" 2>/dev/null; then
    {
        echo ''
        echo '# EchoText command client'
        echo 'export PATH="$HOME/.local/bin:$PATH"'
    } >> "$HOME/.bashrc"
    echo "S'ha afegit $BIN_DIR al PATH a ~/.bashrc"
else
    echo "$BIN_DIR ja està al PATH."
fi

echo ""
echo "=== INSTAL·LACIÓ FINALITZADA ==="
echo ""
echo "Reinicia la terminal o executa:"
echo "  source ~/.bashrc"
echo ""
echo "Llavors podràs usar:"
echo "  echotextcommand [IP_SERVIDOR]"
echo "  echotextcommand --help"
echo ""
