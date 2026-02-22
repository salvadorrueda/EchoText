import os

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
        os.system('echovoice "Apagant l\'ordinador."')
        os.system('systemctl poweroff')
        return True
    elif "suspèn" in text_lower or "suspen" in text_lower:
        print(">>> Ordre 'suspèn' detectada!")
        os.system('echovoice "Suspenent l\'ordinador."')
        os.system('systemctl suspend')
        return True
    
    return False
