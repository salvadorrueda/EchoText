import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import threading
import pyperclip

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
        model_container['model'] = whisper.load_model("turbo")
        print("Model Whisper carregat.")

    loader_thread = threading.Thread(target=load_model_thread)
    loader_thread.start()

    # 2. Enregistrar (mentre el model es carrega)
    try:
        audio_data = record_audio(fs)
        wav.write(temp_filename, fs, audio_data)
    except Exception as e:
        print(f"Error enregistrant àudio: {e}")
        print("Assegura't que tens un micròfon connectat i els drivers instal·lats (ex: libportaudio2).")
        return

    # Esperar que el model acabi de carregar si encara no ho ha fet
    if loader_thread.is_alive():
        print("Esperant que el model acabi de carregar...")
        loader_thread.join()
    
    model = model_container['model']

    # 3. Transcriure
    print("Transcrivint...")
    result = model.transcribe(temp_filename, fp16=False)

    
    print("-" * 30)
    print("Transcripció en viu:")
    text = result["text"].strip()
    print(text)
    print("-" * 30)
    
    # Copiar al porta-retalls
    try:
        pyperclip.copy(text)
        print("✓ Text copiat al porta-retalls! Ja pots fer Ctrl+V.")
    except Exception as e:
        print(f"No s'ha pogut copiar al porta-retalls: {e}")
        print("Assegura't que tens 'xclip' instal·lat (sudo apt install xclip)")
    
    # Netejar fitxer temporal
    if os.path.exists(temp_filename):
        os.remove(temp_filename)

if __name__ == "__main__":
    main()
