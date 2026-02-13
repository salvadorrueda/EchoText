
import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import threading
import time
import pyperclip
import torch
import subprocess

# Custom print function to use ecovoice
def echovoice_print(*args, **kwargs):
    # Construct the message as print would
    msg = " ".join(map(str, args))
    
    # Check if purely separator (lines of - or =) or empty
    clean_msg = msg.strip()
    is_separator = all(c in "-=" for c in clean_msg) if clean_msg else False

    # Original print (using built-in print inside implies we shouldn't shadow it yet, 
    # but if we shadow it, we need access to original. 
    # Python's builtins.print is available via __builtins__.print or simple trick.)
    
    import builtins
    builtins.print(*args, **kwargs)

    if clean_msg and not is_separator:
        try:
            # We assume 'ecovoice' takes the message as a single argument
            subprocess.run(["echovoice", clean_msg], check=False)
        except Exception as e:
            # If ecovoice fails, we don't want to crash the script, just log simple error to stderr or ignore
            # builtins.print(f"Error calling ecovoice: {e}") 
            pass

# Override the built-in print with our custom one
print = echovoice_print

def record_audio(fs=16000):
    print("\nPrem 'ENTER' per començar a enregistrar...")
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

def main():
    fs = 16000  # Whisper prefereix 16kHz
    temp_filename = "live_audio.wav"
    
    # 1. Carregar el model Whisper en paral·lel
    model_container = {} # Per guardar el model carregat pel thread
    
    def load_model_thread():
        print("Carregant el model Whisper (turbo) en segon pla...")
        start_load = time.time()
        model = whisper.load_model("turbo")
        end_load = time.time()
        model_container['model'] = model
        device = next(model.parameters()).device
        print(f"Model Whisper (turbo) carregat correctament en {end_load - start_load:.2f}s.")
        print(f"Dispositiu utilitzat: {device}")

    loader_thread = threading.Thread(target=load_model_thread)
    loader_thread.start()

    try:
        while True:
            # 2. Enregistrar (mentre el model es carrega en la primera iteració)
            try:
                audio_data = record_audio(fs)
                wav.write(temp_filename, fs, audio_data)
            except Exception as e:
                print(f"Error enregistrant àudio: {e}")
                print("Assegura't que tens un micròfon connectat i els drivers instal·lats (ex: libportaudio2).")
                break

            # Esperar que el model acabi de carregar si encara no ho ha fet (només la primera vegada)
            if loader_thread.is_alive():
                print("Esperant que el model acabi de carregar...")
                loader_thread.join()
            
            model = model_container['model']

            # 3. Transcriure
            print("Transcrivint...")
            start_transcription = time.time()
            result = model.transcribe(temp_filename, fp16=False)
            end_transcription = time.time()
            
            print("-" * 30)
            print(f"Transcripció en viu ({end_transcription - start_transcription:.2f}s):")
            text = result["text"].strip()
            print(text)
            print("-" * 30)
            
            # Copiar al porta-retalls
            try:
                pyperclip.copy(text)
                print("✓ Text copiat al porta-retalls! Ja pots fer Ctrl+V.")
            except Exception as e:
                print(f"No s'ha pogut copiar al porta-retalls: {e}")
            
            # Netejar fitxer temporal de l'iteració actual
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                
            print("\n" + "="*30)
            print("Llest per a una nova gravació.")
            print("="*30 + "\n")

    except KeyboardInterrupt:
        print("\nAturant l'escrit...")
    finally:
        # Netejar fitxer temporal si ha quedat
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    main()
