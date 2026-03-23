
#!/usr/bin/env python3
"""
whisper_live_echovoice.py — Transcripció en viu amb retorn de veu via echovoice.

Enregistra fins a ENTER, transcriu localment i llegeix el resultat en veu alta
amb la comanda `echovoice`. El model es carrega en segon pla.

Ús:
    python3 whisper_live_echovoice.py
"""
import os
import sys
import tempfile
import subprocess
import builtins

from lib.venv_activator import activate_venv

if __name__ == "__main__":
    activate_venv(__file__)

import pyperclip
import scipy.io.wavfile as wav
from lib import audio_recorder, model_loader

FS = 16000
LANGUAGE = "ca"


def _echovoice(text: str) -> None:
    """Llegeix `text` en veu alta via la comanda echovoice (sense bloquejar en fallada)."""
    clean = text.strip()
    if not clean or all(c in "-=" for c in clean):
        return
    try:
        subprocess.run(["echovoice", clean], check=False)
    except Exception:
        pass


def main():
    model_container, loader_thread = model_loader.load_model_async()

    try:
        while True:
            builtins.print("\nPrem 'ENTER' per començar a enregistrar...")
            input()
            builtins.print("Enregistrant... Prem 'ENTER' per aturar.")

            try:
                audio_data = audio_recorder.record_full(FS)
            except Exception as e:
                builtins.print(f"Error enregistrant àudio: {e}")
                builtins.print("Assegura't que tens un micròfon connectat.")
                break

            m = model_loader.get_model(model_container, loader_thread)

            with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as tmp:
                wav.write(tmp.name, FS, audio_data)
                builtins.print("Transcrivint...")
                result = m.transcribe(tmp.name, fp16=False, language=LANGUAGE)

            text = result["text"].strip()
            builtins.print("-" * 30)
            builtins.print(text)
            builtins.print("-" * 30)

            _echovoice(text)

            try:
                pyperclip.copy(text)
                builtins.print("✓ Text copiat al porta-retalls!")
            except Exception as e:
                builtins.print(f"No s'ha pogut copiar al porta-retalls: {e}")

            builtins.print("\nLlest per a una nova gravació. (Ctrl+C per sortir)")

    except KeyboardInterrupt:
        builtins.print("\nAturant. Fins aviat!")


if __name__ == "__main__":
    main()
