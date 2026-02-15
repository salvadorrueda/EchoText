# EchoText - OpenAI Whisper Examples

Aquest repositori conté diversos exemples d'ús de **OpenAI Whisper** per a la transcripció de veu a text amb Python en entorns Ubuntu/Linux.

## 🚀 Instal·lació Ràpida

He creat un script que configura automàticament totes les dependències del sistema i l'entorn de Python:

```bash
chmod +x install.sh
./install.sh
```

L'script instal·larà `ffmpeg`, `libportaudio2`, crearà un entorn virtual (`venv`) i instal·larà les llibreries de Python necessàries.

## 🛠️ Com utilitzar els exemples

Abans d'executar qualsevol script, activa l'entorn virtual:

```bash
source venv/bin/activate
```

### 1. Transcripció Bàsica (`whisper_simple.py`)
Transcripció directa d'un fitxer d'àudio anomenat `sample.mp3`.
```bash
python3 whisper_simple.py
```

### 2. Transcripció Avançada (`whisper_advanced.py`)
Detecta l'idioma automàticament i mostra els segments amb marques de temps (timestamps).
```bash
python3 whisper_advanced.py
```

### 3. Transcripció en Viu (`whisper_live.py`)
Enregistra àudio directament des del micròfon i el transcriu quan prems la tecla "Enter".
```bash
python3 whisper_live.py
```

## 🐳 Docker

També pots executar el servidor d'API utilitzant **Docker**. Això és útil si no vols instal·lar dependències localment o per desplegar el servidor en altres màquines.

### 1. Construir la imatge
```bash
docker build -t echotext-server .
```

### 2. Executar el container
```bash
docker run -p 5000:5000 echotext-server
```

### 3. Execució amb GPU (NVIDIA)
Si tens una GPU NVIDIA i vols aprofitar l'acceleració per hardware dins de Docker, necessites tenir instal·lat el [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

Per defecte, el `Dockerfile` actual usa una imatge "slim" basada en CPU. Per usar GPU:
1. Canvia la base del `Dockerfile` a una amb CUDA (ex: `nvidia/cuda:11.8.0-base-ubuntu22.04`).
2. Executa el container amb el flag `--gpus`:
```bash
docker run --gpus all -p 5000:5000 echotext-server
```

## 📋 Requisits del sistema
Els scripts estan provats en **Ubuntu Desktop** i requereixen:
- Python 3.x
- **FFmpeg** (per processar l'àudio) - *Ja inclòs a la imatge Docker.*
- **PortAudio** (per a l'enregistrament en viu)

---
*Creat com a part del projecte EchoText.*
