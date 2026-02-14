#!/usr/bin/env python3
import sys
import os

# Auto-activació de l'entorn virtual (venv) si existeix i no està actiu
def activate_venv():
    # Comprovar si ja estem executant-nos des del venv d'aquest projecte
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(base_dir, "venv", "bin", "python3")
    
    # Si no estem en un venv (sys.prefix == sys.base_prefix) i el venv local existeix
    if sys.prefix == sys.base_prefix and os.path.exists(venv_python):
        # Reiniciar-se amb l'executable del venv
        os.execv(venv_python, [venv_python] + sys.argv)

if __name__ == "__main__":
    # Només ho executem si és el punt d'entrada
    if "client_example.py" in sys.argv[0] or "./client_example.py" in sys.argv[0]:
        activate_venv()

# Importacions que requereixen el venv
import requests
import threading
import queue
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import pyperclip


def record_audio(fs=16000):
    """Enregistra àudio des del micròfon fins que es prem ENTER."""
    print("\n--- Enregistrament de veu ---")
    print("Prem 'ENTER' per començar a enregistrar...")
    input()
    print("Enregistrant... Prem 'ENTER' per aturar.")

    q = queue.Queue()
    stop_event = threading.Event()
    
    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())

    def input_listener():
        input()
        stop_event.set()

    input_thread = threading.Thread(target=input_listener)
    input_thread.start()

    audio_data = []
    
    try:
        with sd.InputStream(samplerate=fs, channels=1, callback=callback):
            while not stop_event.is_set():
                try:
                    data = q.get(timeout=0.1)
                    audio_data.append(data)
                except queue.Empty:
                    continue
    except Exception as e:
        print(f"Error durant l'enregistrament: {e}")
        return None

    if not audio_data:
        print("No s'ha enregistrat cap dada.")
        return None

    print("Enregistrament finalitzat.")
    full_audio = np.concatenate(audio_data, axis=0)
    
    # Crear fitxer temporal
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wav.write(temp_file.name, fs, full_audio)
    temp_file.close()
    
    return temp_file.name


def transcribe_file(filepath, server_url="http://localhost:5000/transcribe"):
    if not os.path.exists(filepath):
        print(f"Error: L'arxiu '{filepath}' no existeix.")
        return

    print(f"Enviant '{filepath}' a {server_url}...")
    
    try:
        with open(filepath, 'rb') as f:
            files = {'file': f}
            data = {'language': 'ca'} # Pots canviar l'idioma aquí
            response = requests.post(server_url, files=files, data=data)
            
        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '').strip()
            print("\n--- Transcripció ---")
            print(text if text else 'No text returned')
            print("--------------------\n")
            
            if text:
                try:
                    pyperclip.copy(text)
                    print("✓ Text copiat al porta-retalls!")
                except Exception as cp_err:
                    print(f"Avís: No s'ha pogut copiar al porta-retalls: {cp_err}")
        else:
            print(f"Error del servidor ({response.status_code}):")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print(f"Error: No s'ha pogut connectar amb el servidor a {server_url}")
    except Exception as e:
        print(f"Error inesperat: {e}")

if __name__ == "__main__":
    server = "localhost"
    if len(sys.argv) > 2:
        server = sys.argv[2]
    elif len(sys.argv) == 2 and not os.path.exists(sys.argv[1]):
        # Si només hi ha un paràmetre i no és un fitxer, assumim que és la IP del servidor
        server = sys.argv[1]
        
    url = f"http://{server}:5000/transcribe"

    audio_file = None
    is_temp = False

    if len(sys.argv) >= 2 and os.path.exists(sys.argv[1]):
        audio_file = sys.argv[1]
    else:
        # Si no hi ha fitxer, enregistrem
        audio_file = record_audio()
        is_temp = True

    if audio_file:
        transcribe_file(audio_file, url)
        
        # Netejar si és temporal
        if is_temp and os.path.exists(audio_file):
            os.remove(audio_file)
    else:
        print("No s'ha pogut obtenir cap àudio per transcriure.")
