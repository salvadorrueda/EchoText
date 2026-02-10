import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import time

def record_audio(duration, fs=16000):
    """Enregistra àudio durant una durada específica."""
    print(f"Escoltant durant {duration} segons...", end="\r")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    return recording

def main():
    fs = 16000
    window_duration = 4  # Finestra total d'anàlisi
    overlap_duration = 2 # Segons que compartim amb l'anterior finestra
    step_duration = window_duration - overlap_duration # Cada quant llegim nou àudio (2s)
    temp_filename = "computer_listen.wav"

    model_name = "turbo" # Utilitzem el model turbo com en els altres scripts

    print(f"Carregant el model Whisper ({model_name})...")
    try:
        model = whisper.load_model(model_name)
    except Exception as e:
        print(f"Error carregant el model: {e}")
        return

    print("Iniciant escolta activa per la paraula clau 'Computer'...")
    print(f"Finestra d'àudio: {window_duration}s | Solapament: {overlap_duration}s")
    print("Prem Ctrl+C per aturar.")

    buffer = np.array([], dtype=np.float32)

    try:
        while True:
            # 1. Enregistrar el fragment nou (step_duration)
            new_audio = record_audio(step_duration, fs)
            
            # Necessitem que sigui float32 i shape (N,) o (N,1) consistent
            if new_audio.ndim > 1:
                new_audio = new_audio.flatten()
            
            # Afegir al buffer
            buffer = np.concatenate((buffer, new_audio))

            # Gestionar la mida del buffer
            # Volem processar quan tinguem almenys window_duration
            if len(buffer) >= int(window_duration * fs):
                
                # Agafem els últims window_duration segons per analitzar
                audio_to_analyze = buffer[-int(window_duration * fs):]
                
                wav.write(temp_filename, fs, audio_to_analyze)

                # 2. Transcriure
                result = model.transcribe(temp_filename, fp16=False, language="en")
                text = result["text"].strip()
                
                if text:
                    print(f"Sentit: {text}")

                # 3. Detectar paraula clau
                normalized_text = text.lower().replace(".", "").replace(",", "").replace("!", "").replace("?", "")
                
                if "computer" in normalized_text:
                    print("\n" + "="*40)
                    print(">>> PARAULA CLAU 'COMPUTER' DETECTADA! <<<")
                    print("="*40 + "\n")
                
                # Mantenim només la part de solapament per a la següent iteració
                # Si volem window=4s i overlap=2s, el step ha estat 2s.
                # Per tant, el buffer ara té (AnticOV + Step).
                # Del que hem analitzat (4s), volem guardar els últims (4s - Step) = Overlap?
                # No exactament. 
                # Si volem finestra lliscant:
                # T0: [AAAA] (4s) -> Analitza.
                # T1: [BBBB] on els primers 2s de B són els últims 2s de A.
                #
                # Per tant, després d'analitzar, hem de deixar al buffer els últims "overlap" segons.
                buffer = buffer[-int(overlap_duration * fs):]


            # Petita pausa potser? No cal si volem continu.

    except KeyboardInterrupt:
        print("\nAturant l'escolta...")
    except Exception as e:
        print(f"\nS'ha produït un error: {e}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    main()
