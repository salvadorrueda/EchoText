import whisper
import os

def transcribe_with_info(file_path, model_type="base"):
    # Carregar model
    print(f"Carregant el model Whisper ({model_type})...")
    model = whisper.load_model(model_type)
    
    # Comprovar si el fitxer existeix
    if not os.path.exists(file_path):
        print(f"Error: El fitxer {file_path} no existeix.")
        return

    # 1. Carregar àudio i fer padding/trimming per a la detecció d'idioma
    audio = whisper.load_audio(file_path)
    audio = whisper.pad_or_trim(audio)

    # 2. Fer el log-Mel spectrogram
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # 3. Detectar l'idioma
    _, probs = model.detect_language(mel)
    detected_lang = max(probs, key=probs.get)
    print(f"Idioma detectat: {detected_lang}")

    # 4. Transcripció completa amb detalls
    print(f"Transcrivint...")
    # options = whisper.DecodingOptions(fp16=False) # Si no tens GPU
    result = model.transcribe(file_path, verbose=False)

    print("-" * 30)
    print(f"Resultat (Idioma: {result['language']}):")
    
    # Imprimir segments amb timestamps
    for segment in result['segments']:
        start = segment['start']
        end = segment['end']
        text = segment['text']
        print(f"[{start:5.2f}s -> {end:5.2f}s] {text}")
    print("-" * 30)

if __name__ == "__main__":
    audio_file = "sample.mp3"
    
    if not os.path.exists(audio_file):
        print(f"Si us plau, posa un fitxer d'àudio anomenat '{audio_file}'")
    else:
        # Pots provar models com 'tiny', 'base', 'small', 'medium', 'large'
        transcribe_with_info(audio_file, model_type="base")
