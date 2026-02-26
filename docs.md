# EchoText Technical Documentation

Aquest document detalla l'arquitectura tècnica, el codi del servidor i la configuració de Docker del projecte EchoText.

## 🚀 Tecnologia Utilitzada

El projecte es basa en les següents tecnologies clau:

- **Python 3.10**: Llenguatge principal de programació.
- **OpenAI Whisper (Model Turbo)**: Sistema de reconeixement de parla (ASR) d'estat de l'art.
- **Flask**: Framework web lleuger per servir l'API.
- **Waitress**: Servidor WSGI de producció per a Flask.
- **PyTorch**: Motor per a l'execució del model Whisper (amb suport CUDA/CPU).
- **Docker**: Plataforma de contenidors per al desplegament aïllat.
- **FFmpeg**: Eina externa indispensable per al processament d'àudio.

## 🖥️ Servidor de l'API (`api_server.py`)

El servidor actua com a pont entre el model Whisper i els clients (web o scripts).

### Càrrega del Model
El servidor utilitza un fil paral·lel o una funció d'inicialització `load_model()` que intenta carregar la versió **"turbo"** de Whisper. 
- Si detecta una GPU NVIDIA (CUDA), l'utilitza automàticament.
- Si no hi ha prou memòria (OOM), intenta carregar el model **"small"** com a alternativa.

### Rutes de l'API

1.  **`/` (GET)**: 
    - Serveix una pàgina HTML generada a partir del fitxer `README.md`.
    - Utilitza la llibreria `markdown` de Python per convertir el format MD a HTML.
    - Inclou estils CSS incrustats per a una presentació neta i llegible.

2.  **`/transcribe` (POST)**:
    - Rep un fitxer d'àudio a través d'un formulari `multipart/form-data`.
    - Guarda temporalment el fitxer per processar-lo amb Whisper.
    - Suporta la detecció automàtica d'idioma o un paràmetre `language` opcional.
    - Retorna un JSON amb el text transcrit.

## 🐳 Docker i Desplegament

La imatge Docker permet desplegar el servidor sense instal·lar dependències a l'host.

### `Dockerfile`
- **Base**: `python:3.10-slim` per mantenir la imatge petita.
- **Dependències del Sistema**: Instal·la `ffmpeg`.
- **Requirements**: Instal·la automàticament totes les llibreries (`flask`, `openai-whisper`, `markdown`, etc.).
- **Codis**: Copia el codi de l'aplicació (`api_server.py`), la llibreria personalitzada (`lib/`) i el `README.md`.

### Persistència del Model
Un dels reptes de Whisper en Docker és la mida del model (1.5 GB). Per evitar descarregar-lo en cada inici:
- S'utilitza un **Docker Volume** (`whisper-models`) muntat a `/root/.cache/whisper`.
- L'script `start_docker_server.sh` automatitza aquesta creació i muntatge.

## 🛠️ Opcions i Configuració

- **CORS**: El servidor està configurat per permetre peticions des de qualsevol origen (`*`), fet necessari per a integracions web directes.
- **Multi-threading**: Flask s'executa darrere de **Waitress**, que gestiona múltiples peticions de forma eficient.
- **Error Handling**: El servidor retorna errors 500 o 503 si el model encara s'està carregant o ha fallat.


Per permetre l'accés extern al servidor:

cloudflared tunnel --url http://localhost:5000

https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/ 
