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


def record_audio(server_url, fs=16000, chunk_duration=5):
    """Enregistra àudio i envia fragments al servidor cada 5 segons."""
    print("\n--- Enregistrament de veu (quasi temps-real) ---")
    print("Prem 'ENTER' per començar a enregistrar...")
    input()
    print(f"Enregistrant... Transcripció cada {chunk_duration}s. Prem 'ENTER' per aturar.")

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

    audio_buffer = []
    full_transcription = []
    
    try:
        with sd.InputStream(samplerate=fs, channels=1, callback=callback):
            while not stop_event.is_set():
                try:
                    data = q.get(timeout=0.1)
                    audio_buffer.append(data)
                except queue.Empty:
                    continue

                total_samples = sum(len(c) for c in audio_buffer)
                
                if total_samples >= fs * chunk_duration:
                    print(".", end="", flush=True)
                    
                    np_audio = np.concatenate(audio_buffer, axis=0)
                    audio_buffer = []
                    
                    # Enviar fragment al servidor
                    with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp:
                        wav.write(temp.name, fs, np_audio)
                        partial_text = transcribe_file(temp.name, server_url, print_header=False)
                        
                        if partial_text:
                            print(f"\n[Chunk]: {partial_text}")
                            full_transcription.append(partial_text)
                            
                            # Actualitzar portapapers amb el que portem
                            current_text = " ".join(full_transcription)
                            try:
                                pyperclip.copy(current_text)
                            except:
                                pass

            # Processar l'últim fragment
            if audio_buffer:
                print("\nProcessant l'últim fragment...")
                np_audio = np.concatenate(audio_buffer, axis=0)
                with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp:
                    wav.write(temp.name, fs, np_audio)
                    partial_text = transcribe_file(temp.name, server_url, print_header=False)
                    if partial_text:
                        print(f"[Final]: {partial_text}")
                        full_transcription.append(partial_text)

    except Exception as e:
        print(f"\nError durant l'enregistrament: {e}")
    finally:
        if input_thread.is_alive():
            print("Prem ENTER per finalitzar si s'ha quedat esperant.")

    return " ".join(full_transcription)


def transcribe_file(filepath, server_url="http://localhost:5000/transcribe", print_header=True):
    if not os.path.exists(filepath):
        print(f"Error: L'arxiu '{filepath}' no existeix.")
        return None

    if print_header:
        print(f"Enviant '{filepath}' a {server_url}...")
    
    try:
        with open(filepath, 'rb') as f:
            files = {'file': f}
            data = {'language': 'ca'} # Pots canviar l'idioma aquí
            response = requests.post(server_url, files=files, data=data)
            
        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '').strip()
            
            if print_header:
                print("\n--- Transcripció ---")
                print(text if text else 'No text returned')
                print("--------------------\n")
                
                if text:
                    try:
                        pyperclip.copy(text)
                        print("✓ Text copiat al porta-retalls!")
                    except Exception as cp_err:
                        print(f"Avís: No s'ha pogut copiar al porta-retalls: {cp_err}")
            
            return text
        else:
            print(f"Error del servidor ({response.status_code}):")
            print(response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"Error: No s'ha pogut connectar amb el servidor a {server_url}")
        return None
    except Exception as e:
        print(f"Error inesperat: {e}")
        return None

if __name__ == "__main__":
    server = "localhost"
    if len(sys.argv) > 2:
        server = sys.argv[2]
    elif len(sys.argv) == 2 and not os.path.exists(sys.argv[1]):
        # Si només hi ha un paràmetre i no és un fitxer, assumim que és la IP del servidor
        server = sys.argv[1]
        
    if ":" in server:
         url = f"http://{server}/transcribe"
    else:
         url = f"http://{server}:5000/transcribe"

    if len(sys.argv) >= 2 and os.path.exists(sys.argv[1]):
        audio_file = sys.argv[1]
        transcribe_file(audio_file, url)
    else:
        # Si no hi ha fitxer, enregistrem en fragments
        final_text = record_audio(url)
        
        if final_text:
            print("\n" + "="*30)
            print("Transcripció Final:")
            print(final_text)
            print("="*30)
            
            try:
                pyperclip.copy(final_text)
                print("✓ Text final copiat al porta-retalls!")
            except:
                pass
        else:
            print("No s'ha pogut obtenir cap àudio per transcriure.")
