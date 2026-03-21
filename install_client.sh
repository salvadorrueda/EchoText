#!/bin/bash

# Script d'instal·lació unificat per als clients remots d'EchoText.
# Per defecte instal·la echotextclient, però també pot instal·lar
# echotextcommand o tots dos.

set -e

GITHUB_RAW="https://raw.githubusercontent.com/salvadorrueda/EchoText/main"
BIN_DIR="$HOME/.local/bin"
DEFAULT_MODE="client"

if [ "$(basename "$0")" = "install_command.sh" ]; then
    DEFAULT_MODE="command"
fi

print_help() {
    echo "Ús: $(basename "$0") [client|command|both]"
    echo ""
    echo "Modes disponibles:"
    echo "  client   Instal·la echotextclient (per defecte)"
    echo "  command  Instal·la echotextcommand"
    echo "  both     Instal·la els dos comandos"
}

MODE="$DEFAULT_MODE"
if [ $# -gt 0 ]; then
    case "$1" in
        client|command|both)
            MODE="$1"
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo "Error: mode no reconegut: $1" >&2
            print_help >&2
            exit 1
            ;;
    esac
fi

ensure_path() {
    if ! grep -qF '$HOME/.local/bin' "$HOME/.bashrc" 2>/dev/null && \
       ! grep -qF "$HOME/.local/bin" "$HOME/.bashrc" 2>/dev/null; then
        {
            echo ''
            echo '# EchoText clients'
            echo 'export PATH="$HOME/.local/bin:$PATH"'
        } >> "$HOME/.bashrc"
        echo "S'ha afegit $BIN_DIR al PATH a ~/.bashrc"
    else
        echo "$BIN_DIR ja està al PATH."
    fi
}

install_variant() {
    local install_dir="$1"
    local command_name="$2"
    local entry_file="$3"
    shift 3

    echo "--- Instal·lant $command_name a $install_dir ---"
    mkdir -p "$install_dir/lib"
    mkdir -p "$BIN_DIR"

    echo "Descarregant fitxers de $command_name..."
    curl -fsSL "$GITHUB_RAW/$entry_file" -o "$install_dir/$entry_file"
    curl -fsSL "$GITHUB_RAW/lib/__init__.py" -o "$install_dir/lib/__init__.py"
    curl -fsSL "$GITHUB_RAW/lib/venv_activator.py" -o "$install_dir/lib/venv_activator.py"

    while [ $# -gt 0 ]; do
        curl -fsSL "$GITHUB_RAW/$1" -o "$install_dir/$1"
        shift
    done

    if [ ! -d "$install_dir/venv" ]; then
        python3 -m venv "$install_dir/venv"
        echo "Entorn virtual creat per a $command_name."
    else
        echo "L'entorn virtual de $command_name ja existeix."
    fi

    "$install_dir/venv/bin/pip" install --upgrade pip -q
    "$install_dir/venv/bin/pip" install requests sounddevice numpy scipy pyperclip -q

    cat > "$BIN_DIR/$command_name" << WRAPPER
#!/bin/bash
exec "$install_dir/venv/bin/python3" "$install_dir/$entry_file" "\$@"
WRAPPER
    chmod +x "$BIN_DIR/$command_name"

    echo "$command_name instal·lat correctament."
}

echo "--- [1/4] Instal·lant dependències de sistema ---"
if command -v apt >/dev/null 2>&1; then
    sudo apt update -q
    sudo apt install -y python3-pip python3-venv libportaudio2 xclip curl
else
    echo "Avís: 'apt' no trobat. Assegura't d'instal·lar 'libportaudio2', 'python3-venv', 'xclip' i 'curl' manualment."
fi

echo "--- [2/4] Preparant la instal·lació ---"
mkdir -p "$BIN_DIR"

echo "--- [3/4] Instal·lant clients seleccionats ---"
case "$MODE" in
    client)
        install_variant "$HOME/.local/share/echotext" "echotextclient" "client_example.py"
        ;;
    command)
        install_variant "$HOME/.local/share/echotext-command" "echotextcommand" "client_command.py" "lib/voice_commands.py"
        ;;
    both)
        install_variant "$HOME/.local/share/echotext" "echotextclient" "client_example.py"
        install_variant "$HOME/.local/share/echotext-command" "echotextcommand" "client_command.py" "lib/voice_commands.py"
        ;;
esac

echo "--- [4/4] Configurant el PATH ---"
ensure_path

echo ""
echo "=== INSTAL·LACIÓ FINALITZADA ==="
echo ""
echo "Reinicia la terminal o executa:"
echo "  source ~/.bashrc"
echo ""
echo "Comandos disponibles segons el mode instal·lat:"
if [ "$MODE" = "client" ] || [ "$MODE" = "both" ]; then
    echo "  echotextclient [IP_SERVIDOR]"
    echo "  echotextclient --help"
fi
if [ "$MODE" = "command" ] || [ "$MODE" = "both" ]; then
    echo "  echotextcommand [IP_SERVIDOR]"
    echo "  echotextcommand --help"
fi
echo ""
