#!/usr/bin/env python3
import sys
import os

# Auto-activació de l'entorn virtual (venv) si existeix i no està actiu
def activate_venv():
    # Comprovar si ja estem executant-nos des del venv d'aquest projecte
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(base_dir, "venv", "bin", "python3")
    
    # Si no estem en un venv (sys.prefix == sys.base_prefix) i el venv local existeix
    if sys.prefix == sys.base_prefix and os.path.exists(venv_python):
        # Reiniciar-se amb l'executable del venv
        os.execv(venv_python, [venv_python] + sys.argv)

if __name__ == "__main__":
    # Només ho executem si és el punt d'entrada
    # Modificat per reflectir el nou nom de l'arxiu
    if "client_command.py" in sys.argv[0] or "./client_command.py" in sys.argv[0]:
        activate_venv()

# Importacions que requereixen el venv
import requests
import threading
import queue
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import pyperclip

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
    print("\nOrdres de veu (després de dir 'Hola'):")
    print("  'terminal'     Obre una nova finestra de terminal.")
    print("  'firefox'      Obre el navegador Firefox.")
    print("  'google'       Obre el navegador Google Chrome.")
    print("  'suspèn'       Suspèn l'ordinador.")
    print("  'apaga'        Apaga l'ordinador.")
    print("  'hora'         Diu l'hora actual.")
    print("  'dia'          Diu la data d'avui.")
    print("="*30)

def record_audio(server_url, fs=16000, chunk_duration=5):
    """Enregistra àudio i envia fragments al servidor cada 5 segons."""
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
                        partial_text = transcribe_file(temp.name, server_url, print_header=False)
                        
                        if partial_text:
                            print(f"\n[Escoltat]: {partial_text}")
                            text_lower = partial_text.lower()
                            
                            # Detecció de la paraula clau "Hola"
                            if "hola" in text_lower:
                                print(">>> Paraula clau 'Hola' detectada!")
                                waiting_for_command = True
                                
                                # Comprovar si l'ordre està en el mateix fragment
                                if "terminal" in text_lower:
                                    print(">>> Ordre 'obra terminal' detectada!")
                                    os.system('gnome-terminal &')
                                    os.system('echovoice "Obrint terminal."')
                                    waiting_for_command = False
                                elif "firefox" in text_lower:
                                    print(">>> Ordre 'Firefox' detectada!")
                                    os.system('firefox &')
                                    os.system('echovoice "Obrint Firefox."')
                                    waiting_for_command = False
                                elif "google" in text_lower:
                                    print(">>> Ordre 'Chrome' detectada!")
                                    os.system('google-chrome &')
                                    os.system('echovoice "Obrint Chrome."')
                                    waiting_for_command = False
                                elif "hora" in text_lower:
                                    print(">>> Ordre 'hora' detectada!")
                                    os.system("echovoice \"Ara són les $(date +'%H:%M')\"")
                                    waiting_for_command = False
                                elif "dia" in text_lower:
                                    print(">>> Ordre 'dia' detectada!")
                                    os.system("echovoice \" Avui és $(date +'%A, %d de %B')\"")
                                    waiting_for_command = False
                                elif "apaga" in text_lower:
                                    print(">>> Ordre 'apaga' detectada!")
                                    os.system('echovoice "Apagant l\'ordinador."')
                                    os.system('systemctl poweroff')
                                    waiting_for_command = False
                                elif "suspèn" in text_lower or "suspen" in text_lower:
                                    print(">>> Ordre 'suspèn' detectada!")
                                    os.system('echovoice "Suspenent l\'ordinador."')
                                    os.system('systemctl suspend')
                                    waiting_for_command = False
                                else:
                                    os.system('echovoice "Hola, amb què puc ajudar?"')
                            
                            # Si ja havíem dit Hola, busquem l'ordre
                            elif waiting_for_command:
                                if "terminal" in text_lower:
                                    print(">>> Ordre 'obra terminal' detectada!")
                                    os.system('gnome-terminal &')
                                    os.system('echovoice "Obrint terminal."')
                                    waiting_for_command = False
                                elif "firefox" in text_lower:
                                    print(">>> Ordre 'Firefox' detectada!")
                                    os.system('firefox &')
                                    os.system('echovoice "Obrint Firefox."')
                                    waiting_for_command = False
                                elif "google" in text_lower:
                                    print(">>> Ordre 'Chrome' detectada!")
                                    os.system('google-chrome &')
                                    os.system('echovoice "Obrint Chrome."')
                                    waiting_for_command = False
                                elif "hora" in text_lower:
                                    print(">>> Ordre 'hora' detectada!")
                                    os.system("echovoice \"Ara són les $(date +'%H:%M')\"")
                                    waiting_for_command = False
                                elif "dia" in text_lower:
                                    print(">>> Ordre 'dia' detectada!")
                                    os.system("echovoice \" Avui és $(date +'%A, %d de %B')\"")
                                    waiting_for_command = False
                                elif "apaga" in text_lower:
                                    print(">>> Ordre 'apaga' detectada!")
                                    os.system('echovoice "Apagant l\'ordinador."')
                                    os.system('systemctl poweroff')
                                    waiting_for_command = False
                                elif "suspèn" in text_lower or "suspen" in text_lower:
                                    print(">>> Ordre 'suspèn' detectada!")
                                    os.system('echovoice "Suspenent l\'ordinador."')
                                    os.system('systemctl suspend')
                                    waiting_for_command = False
                                else:
                                    # Si no detectem res en aquest fragment, mantinguem l'estat waiting_for_command
                                    pass

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
                    partial_text = transcribe_file(temp.name, server_url, print_header=False)
                    if partial_text:
                        print(f"[Final]: {partial_text}")
                        text_lower = partial_text.lower()
                        
                        if "hola" in text_lower:
                            if "terminal" in text_lower:
                                os.system('gnome-terminal &')
                                os.system('echovoice "Obrint terminal."')
                            elif "firefox" in text_lower:
                                os.system('firefox &')
                                os.system('echovoice "Obrint Firefox."')
                            elif "google" in text_lower:
                                os.system('google-chrome &')
                                os.system('echovoice "Obrint Chrome."')
                            elif "hora" in text_lower:
                                os.system("echovoice \"Ara són les $(date +'%H:%M')\"")
                            elif "dia" in text_lower:
                                os.system("echovoice \" Avui és $(date +'%A, %d de %B')\"")
                            elif "apaga" in text_lower:
                                os.system('echovoice "Apagant l\'ordinador."')
                                os.system('systemctl poweroff')
                            elif "suspèn" in text_lower or "suspen" in text_lower:
                                os.system('echovoice "Suspenent l\'ordinador."')
                                os.system('systemctl suspend')
                            else:
                                os.system('echovoice "Hola, amb què puc ajudar?"')
                        elif waiting_for_command:
                             if "terminal" in text_lower:
                                os.system('gnome-terminal &')
                                os.system('echovoice "Obrint terminal."')
                             elif "firefox" in text_lower:
                                os.system('firefox &')
                                os.system('echovoice "Obrint Firefox."')
                             elif "google" in text_lower:
                                os.system('google-chrome &')
                                os.system('echovoice "Obrint Chrome."')
                             elif "hora" in text_lower:
                                os.system("echovoice \"Ara són les $(date +'%H:%M')\"")
                             elif "dia" in text_lower:
                                os.system("echovoice \" Avui és $(date +'%A, %d de %B')\"")
                             elif "apaga" in text_lower:
                                os.system('echovoice "Apagant l\'ordinador."')
                                os.system('systemctl poweroff')
                             elif "suspèn" in text_lower or "suspen" in text_lower:
                                os.system('echovoice "Suspenent l\'ordinador."')
                                os.system('systemctl suspend')
                            
                        full_transcription.append(partial_text)

    except Exception as e:
        print(f"\nError durant l'enregistrament: {e}")
    finally:
        if input_thread.is_alive():
            print("Prem ENTER per finalitzar si s'ha quedat esperant.")

    return " ".join(full_transcription)


def transcribe_file(filepath, server_url="http://localhost:5000/transcribe", print_header=True):
    if not os.path.exists(filepath):
        print(f"Error: L'arxiu '{filepath}' no existeix.")
        return None

    if print_header:
        print(f"Enviant '{filepath}' a {server_url}...")
    
    try:
        with open(filepath, 'rb') as f:
            files = {'file': f}
            data = {'language': 'ca'} # Pots canviar l'idioma aquí
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

if __name__ == "__main__":
    # Check for help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        sys.exit(0)

    server = "localhost"
    if len(sys.argv) > 2:
        server = sys.argv[2]
    elif len(sys.argv) == 2 and not os.path.exists(sys.argv[1]):
        # Si només hi ha un paràmetre i no és un fitxer, assumim que és la IP del servidor
        server = sys.argv[1]
        
    if ":" in server:
         url = f"http://{server}/transcribe"
    else:
         url = f"http://{server}:5000/transcribe"

    if len(sys.argv) >= 2 and os.path.exists(sys.argv[1]):
        audio_file = sys.argv[1]
        transcribe_file(audio_file, url)
    else:
        # Si no hi ha fitxer, enregistrem en fragments
        final_text = record_audio(url)
        
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
