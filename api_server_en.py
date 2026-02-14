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

if __name__ == "__main__" or __name__ == "api_server_en":
    # Només ho executem si és el punt d'entrada per evitar bucles infinits
    # i abans d'importar altres mòduls que podrien faltar al sistema
    if "api_server_en.py" in sys.argv[0] or "./api_server_en.py" in sys.argv[0]:
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
        language = request.form.get('language', 'en') # Default to English
        
        # Guardar fitxer temporalment
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
            file.save(temp.name)
            temp_path = temp.name

        try:
            model = model_container['model']
            # Transcriure - Note: language is forced to 'en' by default unless specified otherwise by client, 
            # but user requested it to "always return transcription in English". 
            # Generally, whisper.transcribe with language='en' will treat audio as English OR translate to English if task='translate'.
            # If the audio is NOT English but we want English text, we should use task="translate".
            # The user said "sempre torni la transcripció en anglès" (always return transcription in English).
            # This implies TRANSLATION if the source is not English.
            # So I should probably set task="translate" if language is 'en'? 
            # Or just rely on `language='en'`? 
            # Whisper `transcribe` has a `task` parameter. Default is `transcribe`.
            # If I set `language='en'`, it expects English audio.
            # If I want to translate ANY audio to English, I need `task='translate'`.
            # Let's assume the user wants translation.
            
            # Use task="translate" to ensure it outputs English regardless of input language
            result = model.transcribe(temp_path, fp16=False, language="en", task="translate")
            text = result["text"].strip()
            
            return jsonify({'text': text, 'language': 'en'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Eliminar fitxer temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == '__main__':
    # Carregar model en un fil o abans d'iniciar el servidor
    # Ho fem abans d'iniciar el servidor per simplificar
    load_model()
    
    # Iniciar servidor Flask accessible des de la xarxa local al port 5001
    print("Iniciant servidor API (English) a 0.0.0.0:5001...")
    app.run(host='0.0.0.0', port=5001, debug=False)
