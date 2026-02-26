#!/usr/bin/env python3
import os
import sys

from lib.venv_activator import activate_venv

if __name__ == "__main__" or __name__ == "api_server":
    # Només ho executem si és el punt d'entrada per evitar bucles infinits
    # i abans d'importar altres mòduls que podrien faltar al sistema
    if "api_server.py" in sys.argv[0] or "./api_server.py" in sys.argv[0]:
        activate_venv(__file__)

import threading
import time
import whisper
import torch
from flask import Flask, request, jsonify
import tempfile
from waitress import serve
import markdown

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    return response

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

@app.route('/', methods=['GET'])
def index():
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="ca">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>EchoText Project</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    margin-top: 24px;
                    margin-bottom: 16px;
                    font-weight: 600;
                    line-height: 1.25;
                }}
                code {{
                    background-color: #f6f8fa;
                    border-radius: 6px;
                    padding: 0.2em 0.4em;
                    font-size: 85%;
                    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
                }}
                pre {{
                    background-color: #f6f8fa;
                    border-radius: 6px;
                    padding: 16px;
                    overflow: auto;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                }}
                a {{
                    color: #0969da;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                table {{
                    border-spacing: 0;
                    border-collapse: collapse;
                    margin-bottom: 16px;
                }}
                th, td {{
                    padding: 6px 13px;
                    border: 1px solid #d0d7de;
                }}
                tr:nth-child(2n) {{
                    background-color: #f6f8fa;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        return html_template
    except Exception as e:
        return f"<h1>Error loading README</h1><p>{{str(e)}}</p>", 500

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
        language = request.form.get('language') # None triggers auto-detection
        
        # Determinar extensió del fitxer original
        import os.path
        ext = os.path.splitext(file.filename)[1] if file.filename else '.wav'
        if not ext:
            ext = '.wav'
        
        # Guardar fitxer temporalment
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
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
    
    # Iniciar servidor Waitress accessible des de la xarxa local
    print("Iniciant servidor API amb Waitress a 0.0.0.0:5000...")
    serve(app, host='0.0.0.0', port=5000)
