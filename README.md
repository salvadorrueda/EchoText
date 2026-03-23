# EchoText

EchoText és un sistema de transcripció de veu a text basat en **OpenAI Whisper** per a Ubuntu/Linux. Inclou un servidor REST, un client en temps quasi-real amb detecció d'ordres de veu, i eines locals de transcripció.

---

## Requisits del sistema

- Ubuntu/Linux amb Python 3.10+
- `ffmpeg` i `libportaudio2`
- (Recomanat) GPU NVIDIA amb CUDA per a millor rendiment

---

## Instal·lació

```bash
chmod +x install.sh
./install.sh
```

L'script instal·la `ffmpeg`, `libportaudio2`, crea un entorn virtual (`venv`) i instal·la totes les dependències de Python.

---

## Estructura del projecte

```
EchoText/
├── api_server.py              # Servidor REST de transcripció (Flask + Waitress)
├── client_command.py          # Client en temps real amb ordres de veu (recomanat)
├── whisper_live.py            # Transcripció en temps real local (sense servidor)
├── whisper_live_echovoice.py  # Transcripció local amb retorn de veu (echovoice)
├── whisper_file.py            # Transcripció d'un fitxer d'àudio local
├── lib/
│   ├── audio_recorder.py      # Captura d'àudio del micròfon
│   ├── server_client.py       # Client HTTP per a api_server.py
│   ├── model_loader.py        # Càrrega de models Whisper amb gestió GPU
│   ├── voice_commands.py      # Reconeixement i execució d'ordres de veu
│   └── venv_activator.py      # Auto-activació del virtualenv
├── Alternatives/              # Alternatives web (Web Speech API, etc.)
├── requirements.txt
├── Dockerfile / docker-compose.yml
└── install.sh / install_client.sh / install_command.sh
```

---

## Casos d'ús principals

### 1. Servidor + Client amb ordres de veu (recomanat)

Arquitectura client-servidor: el servidor carrega Whisper i és accessible des de
qualsevol màquina de la xarxa local. El client enregistra en fragments de 5 s i
envia l'àudio al servidor per transcriure.

**Iniciar el servidor:**
```bash
python3 api_server.py
# o amb Docker:
docker-compose up
```

**Iniciar el client:**
```bash
python3 client_command.py                        # servidor a localhost
python3 client_command.py 192.168.1.10           # servidor a la xarxa local
python3 client_command.py audio.wav              # transcriure un fitxer
python3 client_command.py audio.wav 192.168.1.10 # fitxer + servidor remot
```

**Opcions de client_command.py:**

| Opció | Descripció |
|---|---|
| `-h`, `--help` | Mostra l'ajuda |
| `-m`, `--mute` | Mode menú: executa ordres sense micròfon |
| `--prompt TEXT` | Text inicial per guiar la transcripció de Whisper |

**Flux d'ús normal:**
1. Prem ENTER per començar a escoltar.
2. Di **"Hola"** per activar el reconeixement d'ordres.
3. Di una ordre (veure taula d'ordres més avall).
4. Di **"Adeu"** per finalitzar.

---

### 2. Transcripció local en temps real (sense servidor)

Carrega Whisper directament a la màquina, enregistra en fragments de 5 s i
transcriu localment.

```bash
python3 whisper_live.py
```

---

### 3. Transcripció local amb veu de retorn

Igual que `whisper_live.py` però llegeix el text transcrit en veu alta via la
comanda `echovoice`. Grava un segment sencer (de ENTER a ENTER) en lloc de
fragments curts.

```bash
python3 whisper_live_echovoice.py
```

---

### 4. Transcripció d'un fitxer d'àudio local

Transcriu qualsevol fitxer d'àudio (`.wav`, `.mp3`, etc.) directament amb
Whisper local.

```bash
python3 whisper_file.py audio.wav
python3 whisper_file.py audio.mp3 --verbose          # mostra segments i timestamps
python3 whisper_file.py audio.wav --model small       # força un model concret
```

**Opcions de whisper_file.py:**

| Opció | Descripció |
|---|---|
| `--verbose` | Mostra segments amb timestamps i idioma detectat |
| `--model MODEL` | Nom del model Whisper: `tiny`, `base`, `small`, `medium`, `large`, `turbo` |

---

## Ordres de veu (client_command.py)

Primer di **"Hola"** per activar el reconeixement, després una de les ordres:

| Paraula clau | Acció |
|---|---|
| `terminal` | Obre una nova finestra de terminal |
| `virtualbox` | Obre VirtualBox |
| `matrix` | Arrenca la màquina virtual `vu01` |
| `firefox` | Obre Firefox |
| `google` | Obre Google Chrome |
| `visual` / `studio` / `code` | Obre Visual Studio Code |
| `antigravity` | Obre l'aplicació Antigravity |
| `hora` | Diu l'hora actual en veu alta |
| `dia` | Diu la data d'avui en veu alta |
| `suspèn` | Suspèn l'ordinador |
| `apaga` | Atura els contenidors Docker i apaga l'ordinador |
| `adeu` | Finalitza l'execució de client_command.py |

---

## API del servidor (api_server.py)

El servidor escolta al port `5000`.

### `GET /`
Retorna la documentació del projecte en format HTML.

### `POST /transcribe`
Transcriu un fitxer d'àudio.

**Paràmetres (form-data):**

| Camp | Tipus | Descripció |
|---|---|---|
| `file` | fitxer | Fitxer d'àudio (`.wav`, `.mp3`, etc.) |
| `language` | string | Codi d'idioma (`ca`, `es`, `en`). Opcional: auto-detecció si s'omet |
| `prompt` | string | Text inicial per guiar Whisper. Opcional |

**Resposta JSON:**
```json
{
  "text": "text transcrit",
  "language": "ca",
  "prompt_used": "hola, adeu, terminal, ..."
}
```

**Exemple amb curl:**
```bash
curl -X POST http://localhost:5000/transcribe \
  -F "file=@audio.wav" \
  -F "language=ca"
```

---

## Llibreries compartides (lib/)

| Mòdul | Funció principal |
|---|---|
| `audio_recorder.record_chunks(callback, fs, chunk_duration)` | Enregistra en fragments i crida el callback per cada un |
| `audio_recorder.record_full(fs)` | Enregistra fins a ENTER i retorna numpy array |
| `server_client.transcribe_file(path, url, prompt, print_result)` | Envia WAV al servidor, retorna text |
| `server_client.transcribe_chunk(np_audio, fs, url, prompt)` | Convenience wrapper per a arrays numpy |
| `server_client.check_server_available(url)` | Comprova si el servidor és accessible |
| `server_client.build_server_url(server)` | Converteix IP/hostname en URL completa |
| `model_loader.load_model_async(primary, fallback)` | Inicia càrrega en thread, retorna (container, thread) |
| `model_loader.get_model(container, thread)` | Espera i retorna el model carregat |
| `voice_commands.process_command(text)` | Detecta i executa una ordre de veu |

---

## Instal·lació del client en un altre ordinador

Per usar només el client (sense Whisper ni GPU) des d'una altra màquina:

```bash
chmod +x install_client.sh
./install_client.sh
python3 client_command.py IP_DEL_SERVIDOR
```

---

## Docker

Per executar el servidor dins d'un contenidor:

```bash
docker-compose up          # primer pla
docker-compose up -d       # segon pla
```

El servidor queda accessible a `http://localhost:5000`.

### Persistència del model

Per evitar descarregar el model (~1.5 GB) cada vegada que s'inicia el contenidor:

```bash
chmod +x start_docker_server.sh
./start_docker_server.sh
```

O manualment:
```bash
docker volume create whisper-models
docker run -p 5000:5000 -v whisper-models:/root/.cache/whisper echotext-server
```

### Suport GPU (NVIDIA)

```bash
docker run --gpus all -p 5000:5000 echotext-server
```

---

*EchoText — transcripció de veu en català amb OpenAI Whisper.*
