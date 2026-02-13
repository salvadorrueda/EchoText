#!/usr/bin/env python3
import os
import sys

# Auto-activació del venv si no està actiu
def activate_venv():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_path = os.path.join(script_dir, "venv")
    
    # Si no estem en un venv i el venv local existeix
    if sys.prefix == sys.base_prefix and os.path.isdir(venv_path):
        python_exe = os.path.join(venv_path, "bin", "python3")
        if os.path.isfile(python_exe):
            os.execv(python_exe, [python_exe] + sys.argv)

activate_venv()

import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import threading
import time
import pyperclip
import torch
import queue

def record_and_transcribe(model, fs=16000, chunk_duration=5):
    print("\nPrem 'ENTER' per començar a enregistrar...")
    input()
    print(f"Enregistrant... Transcripció cada {chunk_duration}s. Prem 'ENTER' per aturar.")

    q = queue.Queue()
    stop_event = threading.Event()
    
    def callback(indata, frames, time, status):
        if status:
            print(status)
        q.put(indata.copy())

    # Thread per esperar l'input d'aturada sense bloquejar el principal
    def input_listener():
        input()
        stop_event.set()

    input_thread = threading.Thread(target=input_listener)
    input_thread.start()

    audio_buffer = []
    full_transcription = []
    temp_filename = "temp_live_chunk.wav"
    last_transcription_time = time.time()

    try:
        with sd.InputStream(samplerate=fs, channels=1, callback=callback):
            while not stop_event.is_set():
                try:
                    # Obtenim dades de la cua (sense bloquejar massa temps)
                    data = q.get(timeout=0.1)
                    audio_buffer.append(data)
                except queue.Empty:
                    continue

                # Comprovem si tenim prou àudio (aprox 5 segons)
                # Calculem mostres totals acumulades
                total_samples = sum(len(c) for c in audio_buffer)
                
                if total_samples >= fs * chunk_duration:
                    # Processem el chunk
                    print(".", end="", flush=True) # Feedback visual
                    
                    np_audio = np.concatenate(audio_buffer, axis=0)
                    audio_buffer = [] # Reset del buffer per al següent chunk
                    
                    wav.write(temp_filename, fs, np_audio)
                    
                    # Transcripció ràpida
                    # Utilitzem condition_on_previous_text=False per evitar al·lucinacions en chunks curts
                    result = model.transcribe(temp_filename, fp16=False, language="ca", condition_on_previous_text=False)
                    text = result["text"].strip()
                    
                    if text:
                        print(f"\n[Chunk]: {text}")
                        full_transcription.append(text)
                        
                        # Actualitzem el clipboard amb tot el text fins ara
                        current_full_text = " ".join(full_transcription)
                        try:
                            pyperclip.copy(current_full_text)
                        except:
                            pass

            # En sortir bucle (stop_event), processem el romanent
            if audio_buffer:
                print("\nProcessant l'últim fragment...")
                np_audio = np.concatenate(audio_buffer, axis=0)
                wav.write(temp_filename, fs, np_audio)
                result = model.transcribe(temp_filename, fp16=False, language="ca", condition_on_previous_text=False)
                text = result["text"].strip()
                if text:
                    print(f"[Final]: {text}")
                    full_transcription.append(text)

    except Exception as e:
        print(f"\nError durant l'enregistrament: {e}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        # Assegurar que el thread d'input acaba (potser cal prémer Enter si ha fallat abans)
        if input_thread.is_alive():
            print("Prem ENTER per tancar el programa si s'ha quedat esperant.")

    return " ".join(full_transcription)

def main():
    # 1. Carregar el model Whisper
    print("Carregant el model Whisper (turbo)...")
    model = whisper.load_model("turbo")
    print("Model carregat.")

    while True:
        final_text = record_and_transcribe(model)
        
        print("\n" + "="*30)
        print("Transcripció Final:")
        print(final_text)
        print("="*30)
        
        try:
            pyperclip.copy(final_text)
            print("✓ Text final copiat al porta-retalls!")
        except:
            pass
        
        print("\nVols fer una altra gravació? (Prem Ctrl+C per sortir, o Enter per continuar)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrograma aturat per l'usuari. Fins aviat!")

