import os
import shutil
import subprocess
import sys


def _start_matrix_vm(vm_name="vu01"):
    """Arrenca una VM de VirtualBox amb validacions i missatges d'error clars."""
    if shutil.which("VBoxManage") is None:
        print(">>> Error: VBoxManage no disponible.")
        os.system('echovoice "No trobo VirtualBox instal.lat."')
        return True

    list_result = subprocess.run(
        ["VBoxManage", "list", "vms"],
        capture_output=True,
        text=True,
    )
    if list_result.returncode != 0:
        print(">>> Error consultant les VMs de VirtualBox:", list_result.stderr.strip())
        os.system('echovoice "No puc consultar les maquines virtuals."')
        return True

    if f'"{vm_name}"' not in list_result.stdout:
        print(f">>> Error: VM '{vm_name}' no registrada.")
        os.system('echovoice "No trobo la maquina virtual v zero u."')
        return True

    start_result = subprocess.run(
        ["VBoxManage", "startvm", vm_name, "--type", "gui"],
        capture_output=True,
        text=True,
    )
    if start_result.returncode == 0:
        print(f">>> VM '{vm_name}' arrencada correctament.")
        os.system('echovoice "Arrencant la maquina virtual v zero u."')
        return True

    stderr = (start_result.stderr or "").lower()
    if "already" in stderr and "running" in stderr:
        print(f">>> La VM '{vm_name}' ja estava en execucio.")
        os.system('echovoice "La maquina virtual ja esta en execucio."')
    else:
        print(f">>> Error arrencant la VM '{vm_name}':", start_result.stderr.strip())
        os.system('echovoice "No he pogut arrencar la maquina virtual."')
    return True

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
    elif "virtualbox" in text_lower:
        print(">>> Ordre 'VirtualBox' detectada!")
        os.system('virtualbox &')
        os.system('echovoice "Obrint VirtualBox."')
        return True
    elif "matrix" in text_lower:
        print(">>> Ordre 'Matrix' detectada!")
        return _start_matrix_vm("vu01")
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
