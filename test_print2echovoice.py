#!/usr/bin/env python3
import subprocess
import builtins
import argparse

# Configurar el parseig d'arguments
parser = argparse.ArgumentParser(description="Test per imprimir i opcionalment parlar amb echovoice.")
parser.add_argument("--voice", action="store_true", help="Activa l'ús de echovoice per anunciar els missatges.")
args = parser.parse_args()

# Funció personalitzada per utilitzar echovoice
def echovoice_print(*print_args, **print_kwargs):
    # Construir el missatge tal com ho faria print
    msg = " ".join(map(str, print_args))
    
    # Print original a la consola
    builtins.print(*print_args, **print_kwargs)

    # Si el missatge no està buit, enviar-lo a echovoice
    if msg.strip():
        try:
            subprocess.run(["echovoice", msg], check=False)
        except Exception:
            pass

# Si s'ha passat el flag --voice, sobreescriure el print integrat
if args.voice:
    print = echovoice_print

print("Això és un test")
