import whisper
import os

def transcribe_audio(file_path):
    # Load the base model (you can also use 'tiny', 'small', 'medium', 'large')
    print("Carregant el model Whisper (base)...")
    model = whisper.load_model("base")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: El fitxer {file_path} no existeix.")
        return
    
    # Transcribe (fp16=False per evitar warnings a la CPU)
    print(f"Transcrivint el fitxer: {file_path}")
    result = model.transcribe(file_path, fp16=False)
    
    # Print the result
    print("-" * 30)
    print("Transcripció:")
    print(result["text"])
    print("-" * 30)

if __name__ == "__main__":
    # Pots canviar aquest camí al teu fitxer d'àudio
    audio_file = "sample.mp3" 
    
    # Si no tens un fitxer d'àudio, avisa l'usuari
    if not os.path.exists(audio_file):
        print(f"Si us plau, posa un fitxer d'àudio anomenat '{audio_file}' en aquest directori.")
        print("També pots modificar el script per apuntar a un altre fitxer.")
    else:
        transcribe_audio(audio_file)
