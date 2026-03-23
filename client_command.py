#!/usr/bin/env python3
import sys
import os

from lib.venv_activator import activate_venv

if __name__ == "__main__":
    activate_venv(__file__)

# Importacions que requereixen el venv
import requests
import threading
import queue
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import pyperclip
import webbrowser
from lib import voice_commands

# Vocabulari de paraules clau reconegudes (paraula de despertar + ordres)
COMMAND_KEYWORDS = [
    "hola", "adeu",
    "terminal", "virtualbox", "matrix",
    "firefox", "google", "visual", "studio", "code",
    "antigravity", "hora", "dia", "suspèn", "suspen", "apaga",
]
COMMAND_PROMPT = ", ".join(COMMAND_KEYWORDS)


def print_help():
    """Mostra la informació d'ajuda del programa."""
    print("EchoText Client Command - Ajuda")
    print("="*30)
    print("Aquest script permet transcriure àudio en temps real i executar ordres de veu.")
    print("\nÚs:")
    print("  python3 client_command.py [ARXIU_AUDIO] [IP_SERVIDOR]")
    print("\nArguments:")
    print("  ARXIU_AUDIO    (Opcional) Camí a un arxiu .wav per transcriure.")
    print("  IP_SERVIDOR    (Opcional) IP o hostname del servidor (defecte: localhost).")
    print("\nOpcions:")
    print("  -h, --help     Mostra aquesta ajuda.")
    print("  -m, --mute     Mostra un menú d'ordres i executa sense reconeixement de veu.")
    print("  --prompt PROMPT (Opcional) Text inicial per guiar la transcripció.")
    print("\nOrdres de veu (després de dir 'Hola'):")
    print("  'terminal'     Obre una nova finestra de terminal.")
    print("  'virtualbox'   Obre l'aplicació VirtualBox.")
    print("  'matrix'       Arrenca la màquina virtual vu01.")
    print("  'firefox'      Obre el navegador Firefox.")
    print("  'google'       Obre el navegador Google Chrome.")
    print("  'visual/studio/code' Obre Visual Studio Code.")
    print("  'antigravity'  Obre l'aplicació Antigravity.")
    print("  'adeu'         Finalitza l'execució del programa.")
    print("  'suspèn'       Suspèn l'ordinador.")
    print("  'apaga'        Apaga l'ordinador.")
    print("  'hora'         Diu l'hora actual.")
    print("  'dia'          Diu la data d'avui.")
    print("="*30)

def run_mute_menu():
    """Mostra un menú d'ordres i executa l'opció seleccionada."""
    options = [
        ("terminal", "Obre una nova finestra de terminal"),
        ("virtualbox", "Obre l'aplicació VirtualBox"),
        ("matrix", "Arrenca la màquina virtual vu01"),
        ("firefox", "Obre el navegador Firefox"),
        ("google", "Obre Google Chrome"),
        ("visual studio code", "Obre Visual Studio Code"),
        ("antigravity", "Obre l'aplicació Antigravity"),
        ("hora", "Diu l'hora actual"),
        ("dia", "Diu la data d'avui"),
        ("suspen", "Suspèn l'ordinador"),
        ("apaga", "Apaga l'ordinador"),
        ("adeu", "Sortir del menú"),
    ]

    print("\n--- Mode mute activat ---")
    print("Selecciona una opció per número.")

    while True:
        print("\nOpcions disponibles:")
        for idx, (_, description) in enumerate(options, start=1):
            print(f"  {idx}. {description}")

        choice = input("\nOpció (número o text, 0 per sortir): ").strip().lower()

        if choice in {"0", "q", "quit", "sortir", "exit", "adeu"}:
            print("Sortint del mode mute...")
            break

        command_text = None
        if choice.isdigit():
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(options):
                command_text = options[selected_index][0]
            else:
                print("Opció no vàlida. Torna-ho a provar.")
                continue
        else:
            command_text = choice

        if command_text in {"adeu", "sortir", "exit"}:
            print("Sortint del mode mute...")
            break

        if not voice_commands.process_command(command_text):
            print("No s'ha reconegut cap ordre per aquesta opció.")

def record_audio(server_url, fs=16000, chunk_duration=5, prompt=None):
    """Enregistra àudio i envia fragments al servidor cada 5 segons."""
    # Si no s'ha especificat cap prompt personalitzat, usar el vocabulari d'ordres
    # perquè Whisper només reconegui les paraules clau rellevants.
    if prompt is None:
        prompt = COMMAND_PROMPT

    print("\n--- Enregistrament amb ordres de veu ---")
    print("Paraula clau: 'Hola'")
    print("Prem 'ENTER' per començar a escoltar...")
    input()
    print(f"Escoltant... Transcripció cada {chunk_duration}s. Prem 'ENTER' per aturar.")

    q = queue.Queue()
    stop_event = threading.Event()
    
    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())

    def input_listener():
        input()
        stop_event.set()

    input_thread = threading.Thread(target=input_listener)
    input_thread.start()

    audio_buffer = []
    full_transcription = []
    waiting_for_command = False
    
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
                    
                    # Enviar fragment al servidor
                    with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp:
                        wav.write(temp.name, fs, np_audio)
                        partial_text = transcribe_file(temp.name, server_url, print_header=False, prompt=prompt)
                        
                        if partial_text:
                            print(f"\n[Escoltat]: {partial_text}")
                            text_lower = partial_text.lower()
                            
                            # Detecció de la paraula clau "adeu" per finalitzar
                            if "adeu" in text_lower:
                                print(">>> Paraula clau 'Adeu' detectada! Finalitzant...")
                                os.system('echovoice "Fins aviat!"')
                                stop_event.set()
                                break
                            
                            # Detecció de la paraula clau "Hola"
                            elif "hola" in text_lower:
                                print(">>> Paraula clau 'Hola' detectada!")
                                waiting_for_command = True
                                
                                # Comprovar si l'ordre està en el mateix fragment
                                if voice_commands.process_command(text_lower):
                                    waiting_for_command = False
                                else:
                                    os.system('echovoice "Hola, amb què puc ajudar?"')
                            
                            # Si ja havíem dit Hola, busquem l'ordre
                            elif waiting_for_command:
                                if voice_commands.process_command(text_lower):
                                    waiting_for_command = False

                            full_transcription.append(partial_text)
                            
                            # Actualitzar portapapers amb el que portem
                            current_text = " ".join(full_transcription)
                            try:
                                pyperclip.copy(current_text)
                            except:
                                pass

            # Processar l'últim fragment
            if audio_buffer:
                print("\nProcessant l'últim fragment...")
                np_audio = np.concatenate(audio_buffer, axis=0)
                with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp:
                    wav.write(temp.name, fs, np_audio)
                    partial_text = transcribe_file(temp.name, server_url, print_header=False, prompt=prompt)
                    if partial_text:
                        print(f"[Final]: {partial_text}")
                        text_lower = partial_text.lower()
                        
                        if "adeu" in text_lower:
                            print(">>> Paraula clau 'Adeu' detectada! Finalitzant...")
                            os.system('echovoice "Fins aviat!"')
                        elif "hola" in text_lower:
                            if not voice_commands.process_command(text_lower):
                                os.system('echovoice "Hola, amb què puc ajudar?"')
                        elif waiting_for_command:
                             voice_commands.process_command(text_lower)
                            
                        full_transcription.append(partial_text)

    except Exception as e:
        print(f"\nError durant l'enregistrament: {e}")
    finally:
        if input_thread.is_alive():
            print("Prem ENTER per finalitzar si s'ha quedat esperant.")

    return " ".join(full_transcription)


def transcribe_file(filepath, server_url="http://localhost:5000/transcribe", print_header=True, prompt=None):
    if not os.path.exists(filepath):
        print(f"Error: L'arxiu '{filepath}' no existeix.")
        return None

    if print_header:
        print(f"Enviant '{filepath}' a {server_url}...")
    
    try:
        with open(filepath, 'rb') as f:
            files = {'file': f}
            data = {'language': 'ca'} # Pots canviar l'idioma aquí
            if prompt:
                data['prompt'] = prompt
            response = requests.post(server_url, files=files, data=data)
            
        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '').strip()
            
            if print_header:
                print("\n--- Transcripció ---")
                print(text if text else 'No text returned')
                print("--------------------\n")
                
                if text:
                    try:
                        pyperclip.copy(text)
                        print("✓ Text copiat al porta-retalls!")
                    except Exception as cp_err:
                        print(f"Avís: No s'ha pogut copiar al porta-retalls: {cp_err}")
            
            return text
        else:
            print(f"Error del servidor ({response.status_code}):")
            print(response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"Error: No s'ha pogut connectar amb el servidor a {server_url}")
        return None
    except Exception as e:
        print(f"Error inesperat: {e}")
        return None

def check_server_available(server_url):
    """Comprova si el servidor està disponible abans de començar."""
    try:
        # Peticions GET per veure si respon el port.
        requests.get(server_url, timeout=2)
        return True
    except requests.exceptions.ConnectionError:
        return False
    except Exception:
        # Altres errors com MethodNotAllowed o timeout els donem per bons
        return True

def open_web_speech_api(url):
    """Obre l'alternativa Web Speech API al navegador."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, "Alternatives", "web_speech_API.html")
    print(f"\n[!] No s'ha pogut connectar al servidor a {url}")
    print(f"[!] Obrint l'alternativa Web Speech API al navegador...\n")
    webbrowser.open('file://' + html_path)

if __name__ == "__main__":
    args = sys.argv[1:]

    # Parse options
    mute_mode = False
    prompt = None

    i = 0
    while i < len(args):
        arg = args[i]

        if arg in {"--help", "-h"}:
            print_help()
            sys.exit(0)
        elif arg in {"--mute", "-m"}:
            mute_mode = True
            args.pop(i)
            continue
        elif arg == "--prompt":
            if i + 1 >= len(args):
                print("Error: --prompt requereix un valor.")
                sys.exit(1)
            prompt = args[i + 1]
            args.pop(i)
            args.pop(i)
            continue

        i += 1

    if mute_mode:
        run_mute_menu()
        sys.exit(0)

    server = "localhost"
    if len(args) > 1:
        server = args[1]
    elif len(args) == 1 and not os.path.exists(args[0]):
        # Si només hi ha un paràmetre i no és un fitxer, assumim que és la IP del servidor
        server = args[0]
        
    if server.startswith("http://") or server.startswith("https://"):
         url = server
         if not url.endswith("/transcribe"):
             if url.endswith("/"):
                 url += "transcribe"
             else:
                 url += "/transcribe"
    elif ":" in server:
         url = f"http://{server}/transcribe"
    else:
         url = f"http://{server}:5000/transcribe"

    if len(args) >= 1 and os.path.exists(args[0]):
        audio_file = args[0]
        transcribe_file(audio_file, url, prompt=prompt)
    else:
        # Si no hi ha fitxer, enregistrem en fragments
        if not check_server_available(url):
            open_web_speech_api(url)
            sys.exit(1)
            
        final_text = record_audio(url, prompt=prompt)
        
        if final_text:
            print("\n" + "="*30)
            print("Transcripció Final:")
            print(final_text)
            print("="*30)
            
            try:
                pyperclip.copy(final_text)
                # print("✓ Text final copiat al porta-retalls!")
            except:
                pass
        else:
            print("No s'ha pogut obtenir cap àudio per transcriure.")
