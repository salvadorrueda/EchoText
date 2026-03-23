#!/usr/bin/env python3
#!/usr/bin/env python3
"""
whisper_live.py — Transcripció en temps quasi-real amb model Whisper local.

Enregistra en fragments de 5 s, transcriu localment (sense servidor) i copia
el resultat al porta-retalls. El model es carrega en segon pla per no bloquejar.

Ús:
    python3 whisper_live.py
"""
import os
import sys
import tempfile

from lib.venv_activator import activate_venv

if __name__ == "__main__":
    activate_venv(__file__)

import pyperclip
import scipy.io.wavfile as wav
from lib import audio_recorder, model_loader

FS = 16000
CHUNK_DURATION = 5  # segons
LANGUAGE = "ca"


def _transcribe_chunk(np_audio, model):
    with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as tmp:
        wav.write(tmp.name, FS, np_audio)
        result = model.transcribe(
            tmp.name, fp16=False, language=LANGUAGE, condition_on_previous_text=False
        )
    return result["text"].strip()


def main():
    model_container, loader_thread = model_loader.load_model_async()

    while True:
        if "error" in model_container:
            print("\nNo s'ha pogut carregar cap model. Tancant...")
            break

        full_transcription = []

        print("\nPrem 'ENTER' per començar a enregistrar (model carregant-se en segon pla)...")
        input()
        print(f"Enregistrant... Transcripció cada {CHUNK_DURATION}s. Prem 'ENTER' per aturar.")

        def on_chunk(np_audio, is_final):
            print(".", end="", flush=True)
            m = model_loader.get_model(model_container, loader_thread)
            text = _transcribe_chunk(np_audio, m)
            if text:
                label = "[Final]" if is_final else "[Chunk]"
                print(f"\n{label}: {text}")
                full_transcription.append(text)
                try:
                    pyperclip.copy(" ".join(full_transcription))
                except Exception:
                    pass
            return False

        audio_recorder.record_chunks(on_chunk, fs=FS, chunk_duration=CHUNK_DURATION)

        final_text = " ".join(full_transcription)
        print("\n" + "=" * 30)
        print("Transcripció Final:")
        print(final_text)
        print("=" * 30)
        try:
            pyperclip.copy(final_text)
            print("✓ Text final copiat al porta-retalls!")
        except Exception:
            pass

        print("\nVols fer una altra gravació? (Prem Ctrl+C per sortir, o Enter per continuar)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrograma aturat per l'usuari. Fins aviat!")

