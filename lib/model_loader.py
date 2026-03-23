"""
Mòdul compartit per carregar models Whisper amb gestió de memòria GPU.

Funcions principals:
  - load_whisper_model(): carrega el model en un dict contenidor.
  - load_model_async():   inicia la càrrega en un thread separat.
  - get_model():          espera que el model estigui llest i el retorna.
"""
import time
import threading

import torch
import whisper


def load_whisper_model(model_container: dict, primary: str = "turbo",
                       fallback: str = "small") -> None:
    """
    Carrega el model Whisper `primary` amb fallback a `fallback` si no hi ha
    prou memòria GPU.

    Escriu el resultat a:
        model_container['model']  -> instància del model carregat
        model_container['error']  -> missatge d'error (si ha fallat)
    """
    print(f"Carregant el model Whisper ({primary})...")
    start = time.time()
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        model = whisper.load_model(primary)
        model_container["model"] = model
        elapsed = time.time() - start
        device = next(model.parameters()).device
        print(f"Model Whisper ({primary}) carregat en {elapsed:.2f}s. [{device}]")

    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print(f"ALERTA: Memòria insuficient per a '{primary}'. Provant '{fallback}'...")
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                model = whisper.load_model(fallback)
                model_container["model"] = model
                print(f"Model Whisper ({fallback}) carregat correctament com a alternativa.")
            except Exception as e2:
                print(f"Error fatal carregant model alternatiu: {e2}")
                model_container["error"] = str(e2)
        else:
            print(f"Error carregant el model: {e}")
            model_container["error"] = str(e)
    except Exception as e:
        print(f"Error inesperat carregant el model: {e}")
        model_container["error"] = str(e)


def load_model_async(primary: str = "turbo", fallback: str = "small"):
    """
    Inicia la càrrega del model Whisper en un thread separat.

    Returns:
        (model_container, loader_thread): el dict on es guardarà el model
        i el thread que el carrega.
    """
    model_container = {}
    thread = threading.Thread(
        target=load_whisper_model,
        args=(model_container, primary, fallback),
        daemon=True,
    )
    thread.start()
    return model_container, thread


def get_model(model_container: dict, loader_thread: threading.Thread):
    """
    Espera que el model estigui carregat i el retorna.

    Raises:
        RuntimeError: si la càrrega ha fallat.
    """
    if "model" not in model_container:
        print("\nEsperant que el model acabi de carregar...")
        loader_thread.join()
    if "error" in model_container:
        raise RuntimeError(
            f"No s'ha pogut carregar el model Whisper: {model_container['error']}"
        )
    return model_container["model"]
