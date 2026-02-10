#!/bin/bash

# EchoText Installation Script for GNU/Linux
# This script automates the installation of EchoText and its dependencies.

set -e

REPO_URL="https://github.com/salvadorrueda/EchoText.git"
INSTALL_DIR="$HOME/.echotext"
BIN_DIR="$HOME/.local/bin"

echo "--- Installing EchoText (Whisper Live) ---"

# 1. Install System Dependencies
echo "[1/5] Checking and installing system dependencies..."
if command -v apt-get >/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq ffmpeg libportaudio2 python3-venv xclip git
else
    echo "Warning: apt-get not found. Please ensure 'ffmpeg', 'libportaudio2', 'python3-venv', 'xclip', and 'git' are installed manually."
fi

# 2. Clone or Update Repository
echo "[2/5] Cloning repository to $INSTALL_DIR..."
if [ -d "$INSTALL_DIR" ]; then
    echo "Directory $INSTALL_DIR already exists. Updating..."
    cd "$INSTALL_DIR"
    git pull
else
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 3. Setup Virtual Environment
echo "[3/5] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install openai-whisper sounddevice numpy scipy pyperclip

# 4. Create Global Wrapper Command
echo "[4/5] Setting up global command 'echotext'..."
mkdir -p "$BIN_DIR"

cat << EOF > "$BIN_DIR/echotext"
#!/bin/bash
source "$INSTALL_DIR/venv/bin/activate"
python3 "$INSTALL_DIR/whisper_live.py" "\$@"
EOF

chmod +x "$BIN_DIR/echotext"

# 5. Update PATH in .bashrc
echo "[5/5] Configuring PATH in .bashrc..."
if ! grep -q "$BIN_DIR" "$HOME/.bashrc"; then
    echo "" >> "$HOME/.bashrc"
    echo "# EchoText path" >> "$HOME/.bashrc"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"
    echo "Added $BIN_DIR to PATH in .bashrc"
else
    echo "$BIN_DIR is already in PATH."
fi

echo "--- Installation Complete! ---"
echo "Please restart your terminal or run: source ~/.bashrc"
echo "Then you can use EchoText by typing: echotext"
