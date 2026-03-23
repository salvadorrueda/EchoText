"""
Mòdul compartit per comunicar-se amb el servidor de transcripció (api_server.py).

Funcions principals:
  - transcribe_file():  envia un fitxer WAV al servidor i retorna el text.
  - transcribe_chunk(): convenience wrapper per a fragments numpy.
  - check_server_available(): comprova si el servidor respon.
  - build_server_url():  construeix la URL completa a partir d'IP/hostname.
"""
import os
import tempfile

import requests
import numpy as np
import scipy.io.wavfile as wav

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False

DEFAULT_LANGUAGE = "ca"
DEFAULT_PORT = 5000


def build_server_url(server: str) -> str:
    """
    Construeix la URL de transcripció a partir d'un servidor donat.

    Exemples:
        "localhost"           -> "http://localhost:5000/transcribe"
        "192.168.1.10"        -> "http://192.168.1.10:5000/transcribe"
        "192.168.1.10:8080"   -> "http://192.168.1.10:8080/transcribe"
        "http://myserver.lan" -> "http://myserver.lan/transcribe"
    """
    if server.startswith("http://") or server.startswith("https://"):
        url = server.rstrip("/")
        if not url.endswith("/transcribe"):
            url += "/transcribe"
        return url
    if ":" in server:
        return f"http://{server}/transcribe"
    return f"http://{server}:{DEFAULT_PORT}/transcribe"


def transcribe_file(filepath: str, server_url: str, prompt: str = None,
                    print_result: bool = False) -> str | None:
    """
    Envia un fitxer WAV al servidor i retorna el text transcrit.

    Args:
        filepath:     Camí a un fitxer WAV existent.
        server_url:   URL completa de l'endpoint de transcripció.
        prompt:       Text inicial per guiar Whisper (opcional).
        print_result: Si True, imprimeix el resultat i el copia al porta-retalls.

    Returns:
        El text transcrit, o None si hi ha hagut un error.
    """
    if not os.path.exists(filepath):
        print(f"Error: L'arxiu '{filepath}' no existeix.")
        return None

    try:
        with open(filepath, "rb") as f:
            data = {"language": DEFAULT_LANGUAGE}
            if prompt:
                data["prompt"] = prompt
            response = requests.post(server_url, files={"file": f}, data=data)

        if response.status_code == 200:
            text = response.json().get("text", "").strip()
            if print_result:
                print("\n--- Transcripció ---")
                print(text if text else "(sense text)")
                print("--------------------\n")
                if text and _PYPERCLIP:
                    try:
                        import pyperclip
                        pyperclip.copy(text)
                        print("✓ Text copiat al porta-retalls!")
                    except Exception as cp_err:
                        print(f"Avís: No s'ha pogut copiar al porta-retalls: {cp_err}")
            return text

        print(f"Error del servidor ({response.status_code}): {response.text}")
        return None

    except requests.exceptions.ConnectionError:
        print(f"Error: No s'ha pogut connectar amb el servidor a {server_url}")
        return None
    except Exception as e:
        print(f"Error inesperat: {e}")
        return None


def transcribe_chunk(np_audio: np.ndarray, fs: int, server_url: str,
                     prompt: str = None) -> str | None:
    """
    Escriu un fragment numpy com a WAV temporal i el transcriu via servidor.
    El fitxer temporal s'elimina automàticament.
    """
    with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as tmp:
        wav.write(tmp.name, fs, np_audio)
        return transcribe_file(tmp.name, server_url, prompt=prompt)


def check_server_available(server_url: str) -> bool:
    """
    Comprova si el servidor de transcripció és accessible.

    Returns:
        True si el servidor respon (fins i tot amb errors HTTP),
        False si la connexió falla completament.
    """
    try:
        requests.get(server_url, timeout=2)
        return True
    except requests.exceptions.ConnectionError:
        return False
    except Exception:
        return True  # Errors HTTP (405, etc.) indiquen que el servidor és viu
