import os
import sys

def process_command(text_lower):
    """
    Processa el text per trobar i executar ordres.
    Retorna True si s'ha executat alguna ordre, False en cas contrari.
    """
    if "terminal" in text_lower:
        print(">>> Ordre 'obra terminal' detectada!")
        os.system('gnome-terminal &')
        os.system('echovoice "Obrint terminal."')
        return True
    elif "firefox" in text_lower:
        print(">>> Ordre 'Firefox' detectada!")
        os.system('firefox &')
        os.system('echovoice "Obrint Firefox."')
        return True
    elif "antigravity" in text_lower:
        print(">>> Ordre 'Antigravity' detectada!")
        os.system('antigravity &')
        os.system('echovoice "Obrint Antigravity."')
        return True
    elif "google" in text_lower:
        print(">>> Ordre 'Chrome' detectada!")
        os.system('google-chrome &')
        os.system('echovoice "Obrint Chrome."')
        return True
    elif "hora" in text_lower:
        print(">>> Ordre 'hora' detectada!")
        os.system("echovoice \"Ara són les $(date +'%H:%M')\"")
        return True
    elif "dia" in text_lower:
        print(">>> Ordre 'dia' detectada!")
        os.system("echovoice \" Avui és $(date +'%A, %d de %B')\"")
        return True
    elif "apaga" in text_lower:
        print(">>> Ordre 'apaga' detectada!")
        os.system('echovoice "Aturant contenidors docker i apagant l\'sistema."')
        # Aturar tots els contenidors docker (si n'hi ha)
        os.system('docker stop $(docker ps -q) 2>/dev/null')
        
        # Detectar si és GNOME Desktop
        is_gnome = "GNOME" in os.environ.get("XDG_CURRENT_DESKTOP", "")
        
        if is_gnome:
            # Utilitzar gnome-session-quit per a una millor integració amb GNOME
            os.system('gnome-session-quit --power-off --no-prompt')
        else:
            # Apagar el sistema via systemctl
            os.system('systemctl poweroff')
        
        # Aturar l'script actual
        sys.exit(0)
        return True
    elif "suspèn" in text_lower or "suspen" in text_lower:
        print(">>> Ordre 'suspèn' detectada!")
        os.system('echovoice "Suspenent l\'ordinador."')
        os.system('systemctl suspend')
        return True
    
    return False
