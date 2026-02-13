import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import threading
import time
import subprocess
import torch

def record_audio(fs=16000):
    print("\nPrem 'ENTER' per començar a enregistrar el comandament...")
    input()
    
    print("Enregistrant... Prem 'ENTER' per aturar.")
    
    recording = []
    stop_event = threading.Event()

    def callback(indata, frames, time, status):
        if status:
            print(status)
        recording.append(indata.copy())

    # Iniciar la gravació en un stream
    with sd.InputStream(samplerate=fs, channels=1, callback=callback):
        input() # Espera a que l'usuari premi Enter de nou
        stop_event.set()

    print("Enregistrament finalitzat.")
    
    # Convertir la llista de chunks a un array de numpy
    audio_data = np.concatenate(recording, axis=0)
    return audio_data

def process_command(text):
    text = text.lower().strip()
    print(f"Comandament detectat: '{text}'")
    
    # Comandament: Obre terminal
    if "obre terminal" in text:
        print("✓ Executant: Obrint terminal...")
        try:
            # Utilitzem x-terminal-emulator per ser més genèrics, o gnome-terminal com a fallback
            subprocess.Popen(["x-terminal-emulator"], start_new_session=True)
        except FileNotFoundError:
            try:
                subprocess.Popen(["gnome-terminal"], start_new_session=True)
            except Exception as e:
                print(f"Error obrint el terminal: {e}")
        return True
    
    return False

def main():
    fs = 16000  # Whisper prefereix 16kHz
    temp_filename = "command_audio.wav"
    
    # 1. Carregar el model Whisper en paral·lel
    model_container = {} 
    
    def load_model_thread():
        print("Carregant el model Whisper (turbo) per a comandaments...")
        start_load = time.time()
        model = whisper.load_model("turbo")
        end_load = time.time()
        model_container['model'] = model
        device = next(model.parameters()).device
        print(f"Model Whisper (turbo) carregat en {end_load - start_load:.2f}s.")
        print(f"Dispositiu: {device}")

    loader_thread = threading.Thread(target=load_model_thread)
    loader_thread.start()

    try:
        while True:
            # 2. Enregistrar
            try:
                audio_data = record_audio(fs)
                wav.write(temp_filename, fs, audio_data)
            except Exception as e:
                print(f"Error enregistrant àudio: {e}")
                break

            # Esperar que el model acabi de carregar si encara no ho ha fet
            if loader_thread.is_alive():
                print("Esperant que el model acabi de carregar...")
                loader_thread.join()
            
            model = model_container['model']

            # 3. Transcriure
            print("Processant comandament de veu...")
            result = model.transcribe(temp_filename, fp16=False)
            text = result["text"].strip()
            
            # 4. Processar el text per trobar comandaments
            if not process_command(text):
                print("No s'ha reconegut cap comandament d'acció.")
            
            # Netejar fitxer temporal
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                
            print("\n" + "="*30)
            print("Llest per al següent comandament.")
            print("="*30 + "\n")

    except KeyboardInterrupt:
        print("\nAturant l'escrit de comandaments...")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    main()
