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

def record_and_transcribe(model_container, loader_thread, fs=16000, chunk_duration=5):
    print("\nPrem 'ENTER' per començar a enregistrar (el model es carrega en segon pla)...")
    input()
    print(f"Enregistrant... Transcripció cada {chunk_duration}s. Prem 'ENTER' per aturar.")

    q = queue.Queue()
    stop_event = threading.Event()
    
    def callback(indata, frames, time, status):
        if status:
            print(status)
        q.put(indata.copy())

    def input_listener():
        input()
        stop_event.set()

    input_thread = threading.Thread(target=input_listener)
    input_thread.start()

    audio_buffer = []
    full_transcription = []
    temp_filename = "temp_live_chunk.wav"
    
    #Funció auxiliar per obtenir el model
    def get_model():
        if 'model' not in model_container:
            print("\nEsperant que el model acabi de carregar...")
            loader_thread.join()
        return model_container['model']

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
                    
                    wav.write(temp_filename, fs, np_audio)
                    
                    model = get_model() # Assegurar que tenim model
                    
                    result = model.transcribe(temp_filename, fp16=False, language="ca", condition_on_previous_text=False)
                    text = result["text"].strip()
                    
                    if text:
                        print(f"\n[Chunk]: {text}")
                        full_transcription.append(text)
                        
                        current_full_text = " ".join(full_transcription)
                        try:
                            pyperclip.copy(current_full_text)
                        except:
                            pass

            if audio_buffer:
                print("\nProcessant l'últim fragment...")
                np_audio = np.concatenate(audio_buffer, axis=0)
                wav.write(temp_filename, fs, np_audio)
                
                model = get_model() # Assegurar que tenim model
                
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
        if input_thread.is_alive():
            print("Prem ENTER per tancar el programa si s'ha quedat esperant.")

    return " ".join(full_transcription)

def main():
    # 1. Carregar el model Whisper en paral·lel
    model_container = {} 
    
    def load_model_thread():
        print("Carregant el model Whisper (turbo) en segon pla...")
        start_load = time.time()
        
        try:
            # Intentar netejar la memòria cau de CUDA abans
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            model = whisper.load_model("turbo")
            end_load = time.time()
            model_container['model'] = model
            print(f"\nModel Whisper (turbo) carregat correctament en {end_load - start_load:.2f}s.")
            
        except RuntimeError as e:
            if "out of memory" in str(e):
                print("\nALERTA: Memòria CUDA insuficient per al model 'turbo'. Intentant amb 'small'...")
                try:
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    model = whisper.load_model("small")
                    model_container['model'] = model
                    print("\nModel Whisper (small) carregat correctament com a alternativa.")
                except Exception as e2:
                    print(f"\nError fatal carregant el model alternatiu: {e2}")
                    model_container['error'] = str(e2)
            else:
                print(f"\nError carregant el model: {e}")
                model_container['error'] = str(e)
        except Exception as e:
             print(f"\nError inesperat carregant el model: {e}")
             model_container['error'] = str(e)

    loader_thread = threading.Thread(target=load_model_thread)
    loader_thread.start()

    while True:
        # Check d'errors abans de començar
        if 'error' in model_container:
            print("\nNo s'ha pogut carregar cap model. Tancant...")
            break
            
        final_text = record_and_transcribe(model_container, loader_thread)
        
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

