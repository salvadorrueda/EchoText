"""
Mòdul compartit per a la captura d'àudio del micròfon.

Dues funcions principals:
  - record_chunks(): enregistra en fragments i crida un callback per fragment.
  - record_full():   enregistra fins a un segon ENTER i retorna tot l'àudio.
"""
import sys
import threading
import queue

import sounddevice as sd
import numpy as np


def record_chunks(chunk_callback, fs=16000, chunk_duration=5):
    """
    Enregistra àudio en fragments de `chunk_duration` segons.

    Per a cada fragment llest crida:
        chunk_callback(np_audio: np.ndarray, is_final: bool) -> bool | None

    Si el callback retorna True l'enregistrament s'atura immediatament
    (útil per a la detecció d'una paraula de finalització).

    Bloqueja fins que l'usuari prem ENTER o el callback demana aturada.
    """
    q = queue.Queue()
    stop_event = threading.Event()

    def _audio_callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())

    def _input_listener():
        input()
        stop_event.set()

    input_thread = threading.Thread(target=_input_listener, daemon=True)
    input_thread.start()

    audio_buffer = []
    try:
        with sd.InputStream(samplerate=fs, channels=1, callback=_audio_callback):
            while not stop_event.is_set():
                try:
                    data = q.get(timeout=0.1)
                    audio_buffer.append(data)
                except queue.Empty:
                    continue

                if sum(len(c) for c in audio_buffer) >= fs * chunk_duration:
                    chunk = np.concatenate(audio_buffer, axis=0)
                    audio_buffer = []
                    if chunk_callback(chunk, False):
                        stop_event.set()
                        break

            # Fragment final (àudio que queda al buffer)
            if audio_buffer:
                chunk = np.concatenate(audio_buffer, axis=0)
                chunk_callback(chunk, True)

    except Exception as e:
        print(f"\nError durant l'enregistrament: {e}", file=sys.stderr)
        raise
    finally:
        if input_thread.is_alive():
            print("Prem ENTER per finalitzar si s'ha quedat esperant.")


def record_full(fs=16000):
    """
    Enregistra àudio fins que l'usuari prem ENTER.

    Retorna tot l'àudio capturat com a np.ndarray de forma (N, 1).
    El caller ha de gestionar els missatges d'inici/aturada abans de cridar aquesta funció.
    """
    recording = []

    def _callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        recording.append(indata.copy())

    with sd.InputStream(samplerate=fs, channels=1, callback=_callback):
        input()  # Espera que l'usuari premi ENTER per aturar

    if not recording:
        return np.zeros((0, 1), dtype=np.float32)
    return np.concatenate(recording, axis=0)
