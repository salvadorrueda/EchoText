import sys
import os

def activate_venv(script_path):
    """
    Auto-activació de l'entorn virtual (venv) si existeix i no està actiu.
    """
    # Comprovar si ja estem executant-nos des del venv d'aquest projecte
    base_dir = os.path.dirname(os.path.abspath(script_path))
    venv_python = os.path.join(base_dir, "venv", "bin", "python3")
    
    # Si no estem en un venv (sys.prefix == sys.base_prefix) i el venv local existeix
    if sys.prefix == sys.base_prefix and os.path.exists(venv_python):
        # Reiniciar-se amb l'executable del venv
        os.execv(venv_python, [venv_python] + sys.argv)
