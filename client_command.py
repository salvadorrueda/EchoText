#!/usr/bin/env python3
#!/usr/bin/env python3
import sys
import os

from lib.venv_activator import activate_venv

if __name__ == "__main__":
    activate_venv(__file__)

import pyperclip
import webbrowser
from lib import voice_commands, audio_recorder, server_client

# Vocabulari de paraules clau reconegudes (paraula de despertar + ordres)
COMMAND_KEYWORDS = [
    "hola", "adeu",
    "terminal", "virtualbox", "matrix",
    "firefox", "google", "visual", "studio", "code",
    "antigravity", "hora", "dia", "suspèn", "suspen", "apaga",
]
COMMAND_PROMPT = ", ".join(COMMAND_KEYWORDS)


def _print_help():
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

def _run_mute_menu():
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

def _record_audio(server_url, fs=16000, chunk_duration=5, prompt=None):
    """Enregistra àudio en fragments i processa ordres de veu en temps quasi-real."""
    if prompt is None:
        prompt = COMMAND_PROMPT

    print("\n--- Enregistrament amb ordres de veu ---")
    print("Paraula clau d'activació: 'Hola'  |  Per sortir: 'Adeu'")
    print("Prem 'ENTER' per començar a escoltar...")
    input()
    print(f"Escoltant... Transcripció cada {chunk_duration}s. Prem 'ENTER' per aturar.")

    full_transcription = []
    waiting_for_command = [False]

    def on_chunk(np_audio, is_final):
        label = "[Final]" if is_final else "[Escoltat]"
        print(".", end="", flush=True)

        partial_text = server_client.transcribe_chunk(np_audio, fs, server_url, prompt=prompt)
        if not partial_text:
            return False

        print(f"\n{label}: {partial_text}")
        text_lower = partial_text.lower()

        if "adeu" in text_lower:
            print(">>> Paraula clau 'Adeu' detectada! Finalitzant...")
            os.system('echovoice "Fins aviat!"')
            return True  # Atura l'enregistrament

        if "hola" in text_lower:
            print(">>> Paraula clau 'Hola' detectada!")
            waiting_for_command[0] = True
            if not voice_commands.process_command(text_lower):
                os.system('echovoice "Hola, amb què puc ajudar?"')
            else:
                waiting_for_command[0] = False
        elif waiting_for_command[0]:
            if voice_commands.process_command(text_lower):
                waiting_for_command[0] = False

        full_transcription.append(partial_text)
        try:
            pyperclip.copy(" ".join(full_transcription))
        except Exception:
            pass
        return False

    audio_recorder.record_chunks(on_chunk, fs=fs, chunk_duration=chunk_duration)
    return " ".join(full_transcription)
if __name__ == "__main__":
    args = sys.argv[1:]
def _open_web_speech_api(url):
    """Obre l'alternativa Web Speech API al navegador si el servidor no està disponible."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, "Alternatives", "web_speech_API.html")
    print(f"\n[!] No s'ha pogut connectar al servidor a {url}")
    print("[!] Obrint l'alternativa Web Speech API al navegador...\n")
    webbrowser.open("file://" + html_path)


    # Parse options
    mute_mode = False
    prompt = None

    i = 0
    while i < len(args):
        arg = args[i]

        if arg in {"--help", "-h"}:
            _print_help()
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
        _run_mute_menu()
        sys.exit(0)

    server = "localhost"
    if len(args) > 1:
        server = args[1]
    elif len(args) == 1 and not os.path.exists(args[0]):
        server = args[0]

    url = server_client.build_server_url(server)

    if len(args) >= 1 and os.path.exists(args[0]):
        audio_file = args[0]
        server_client.transcribe_file(audio_file, url, prompt=prompt, print_result=True)
    else:
        if not server_client.check_server_available(url):
            _open_web_speech_api(url)
            sys.exit(1)
            
        final_text = _record_audio(url, prompt=prompt)
        
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
