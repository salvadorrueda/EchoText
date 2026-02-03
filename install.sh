#!/bin/bash

# Script d'instal·lació per a exemples d'OpenAI Whisper en Ubuntu Desktop

# Exit on error
set -e

echo "--- Iniciant la instal·lació de dependències de sistema ---"
sudo apt update
sudo apt install -y python3-pip python3-venv ffmpeg libportaudio2

echo "--- Creant l'entorn virtual (venv) ---"
if [ -d "venv" ]; then
    echo "L'entorn virtual ja existeix. Saltant pas."
else
    python3 -m venv venv
    echo "Entorn virtual creat."
fi

echo "--- Instal·lant paquets de Python dins del venv ---"
source venv/bin/activate

# Actualitzem pip primer
pip install --upgrade pip

# Instal·lem les dependències principals
pip install openai-whisper setuptools-rust sounddevice scipy numpy

echo ""
echo "--- INSTAL·LACIÓ FINALITZADA AMB ÈXIT ---"
echo ""
echo "Per utilitzar els scripts, recorda activar l'entorn virtual:"
echo "source venv/bin/activate"
echo ""
echo "Després pots executar:"
echo "- python3 whisper_simple.py   (Exemple bàsic)"
echo "- python3 whisper_advanced.py (Amb timestamps i detecció d'idioma)"
echo "- python3 whisper_live.py     (Enregistrament en viu pel micròfon)"
echo "----------------------------------------"
