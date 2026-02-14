#!/usr/bin/env python3
import os
import sys

# Auto-activació de l'entorn virtual (venv) si existeix i no està actiu
def activate_venv():
    # Comprovar si ja estem executant-nos des del venv d'aquest projecte
    # Basat en si el path de l'executable conté 'venv/bin/python'
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(base_dir, "venv", "bin", "python3")
    
    # Si l'entorn virtual existeix i no el fem servir actualment, ens reiniciem
    # També comprovem VIRTUAL_ENV per seguretat, tot i que l'executable és més directe
    if os.path.exists(venv_python) and sys.executable != venv_python:
        print(f"Activant entorn virtual: {venv_python}")
        os.execv(venv_python, [venv_python] + sys.argv)

if __name__ == "__main__" or __name__ == "api_server":
    # Només ho executem si és el punt d'entrada per evitar bucles infinits
    # i abans d'importar altres mòduls que podrien faltar al sistema
    if "api_server.py" in sys.argv[0] or "./api_server.py" in sys.argv[0]:
        activate_venv()

import threading
import time
import whisper
import torch
from flask import Flask, request, jsonify
import tempfile

app = Flask(__name__)

# Variable global per emmagatzemar el model
model_container = {}

def load_model():
    """Carrega el model Whisper en memòria."""
    print("Carregant el model Whisper (turbo)...")
    start_load = time.time()
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("Utilitzant CUDA (GPU).")
        else:
            print("Utilitzant CPU.")
            
        model = whisper.load_model("turbo")
        model_container['model'] = model
        end_load = time.time()
        print(f"Model Whisper (turbo) carregat correctament en {end_load - start_load:.2f}s.")
        
    except RuntimeError as e:
        if "out of memory" in str(e):
            print("ALERTA: Memòria insuficient per al model 'turbo'. Intentant amb 'small'...")
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                model = whisper.load_model("small")
                model_container['model'] = model
                print("Model Whisper (small) carregat correctament.")
            except Exception as e2:
                print(f"Error fatal carregant model alternatiu: {e2}")
                model_container['error'] = str(e2)
        else:
            print(f"Error carregant el model: {e}")
            model_container['error'] = str(e)
    except Exception as e:
        print(f"Error inesperat carregant el model: {e}")
        model_container['error'] = str(e)

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    # Comprovar estat del model
    if 'error' in model_container:
        return jsonify({'error': f"Model failed to load: {model_container['error']}"}), 500
    if 'model' not in model_container:
        return jsonify({'error': 'Model is still loading, please try again later'}), 503

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        language = request.form.get('language', 'ca') # Per defecte català
        
        # Guardar fitxer temporalment
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
            file.save(temp.name)
            temp_path = temp.name

        try:
            model = model_container['model']
            # Transcriure
            result = model.transcribe(temp_path, fp16=False, language=language)
            text = result["text"].strip()
            
            return jsonify({'text': text, 'language': language})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Eliminar fitxer temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == '__main__':
    # Carregar model en un fil o abans d'iniciar el servidor
    # Ho fem abans d'iniciar el servidor per simplificar, tot i que bloquejarà l'inici fins que carregui
    load_model()
    
    # Iniciar servidor Flask accessible des de la xarxa local
    print("Iniciant servidor API a 0.0.0.0:5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
