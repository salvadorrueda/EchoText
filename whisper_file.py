#!/usr/bin/env python3
"""
whisper_file.py — Transcripció d'un fitxer d'àudio amb Whisper local.

Fusió de whisper_simple.py i whisper_advanced.py. Per defecte mostra el text
complert; amb --verbose mostra segments amb timestamps i l'idioma detectat.

Ús:
    python3 whisper_file.py <fitxer_audio> [--verbose] [--model MODEL]

Exemples:
    python3 whisper_file.py audio.wav
    python3 whisper_file.py audio.mp3 --verbose
    python3 whisper_file.py audio.wav --model small
"""
import os
import sys

from lib.venv_activator import activate_venv

if __name__ == "__main__":
    activate_venv(__file__)

import whisper
import torch


DEFAULT_MODEL = "turbo"


def transcribe(file_path: str, model_name: str = DEFAULT_MODEL,
               verbose: bool = False) -> str | None:
    """
    Transcriu un fitxer d'àudio.

    Args:
        file_path:  Camí al fitxer d'àudio.
        model_name: Nom del model Whisper (tiny, base, small, medium, large, turbo).
        verbose:    Si True, mostra segments amb timestamps i idioma detectat.

    Returns:
        El text transcrit, o None si el fitxer no existeix.
    """
    if not os.path.exists(file_path):
        print(f"Error: El fitxer '{file_path}' no existeix.")
        return None

    print(f"Carregant el model Whisper ({model_name})...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_name, device=device)

    print(f"Transcrivint '{file_path}'...")
    result = model.transcribe(file_path, fp16=(device == "cuda"))

    print("-" * 40)
    if verbose:
        print(f"Idioma detectat: {result.get('language', 'desconegut')}")
        print()
        for seg in result.get("segments", []):
            print(f"[{seg['start']:6.2f}s -> {seg['end']:6.2f}s]  {seg['text'].strip()}")
    else:
        print(result["text"].strip())
    print("-" * 40)

    return result["text"].strip()


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] in {"-h", "--help"}:
        print(__doc__)
        sys.exit(0)

    verbose = "--verbose" in args
    if verbose:
        args.remove("--verbose")

    model_name = DEFAULT_MODEL
    if "--model" in args:
        idx = args.index("--model")
        if idx + 1 < len(args):
            model_name = args[idx + 1]
            args.pop(idx)
            args.pop(idx)
        else:
            print("Error: --model requereix un valor (p.ex. --model small).")
            sys.exit(1)

    if not args:
        print("Error: cal especificar un fitxer d'àudio.")
        print("Ús: python3 whisper_file.py <fitxer_audio> [--verbose] [--model MODEL]")
        sys.exit(1)

    transcribe(args[0], model_name=model_name, verbose=verbose)
