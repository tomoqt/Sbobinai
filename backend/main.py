from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import openai
from pydub import AudioSegment

# Load environment variables
load_dotenv()

# Initialize OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Environment variables
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o-mini")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/test_upload_audio")
async def test_upload_audio(file: UploadFile = File(...)):
    file_path = os.path.join("uploads", file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Convert Opus to WAV for Whisper API
    audio = AudioSegment.from_file(file_path, format="opus")
    wav_path = file_path.rsplit(".", 1)[0] + ".wav"
    audio.export(wav_path, format="wav")
    
    with open(wav_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe(WHISPER_MODEL, audio_file)
    
    # Clean up temporary files
    os.remove(file_path)
    os.remove(wav_path)
    
    chunks = split_text(transcript['text'], CHUNK_SIZE)
    processed_chunks = []
    for chunk in chunks:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "Sei un assistente utile che struttura il testo in un formato markdown leggibile."},
                {"role": "user", "content": f"Per favore, struttura questo testo in un formato markdown leggibile, mantenendo il contenuto estremamente fedele all'originale: {chunk}"}
            ]
        )
        processed_chunks.append(response.choices[0].message['content'])
    
    final_text = "\n\n".join(processed_chunks)
    
    processed_file_path = os.path.join("processed", f"{file.filename}.md")
    with open(processed_file_path, "w") as f:
        f.write(final_text)
    
    return {"message": "Audio elaborato con successo", "filename": f"{file.filename}.md"}

@app.get("/test_get_text/{filename}")
async def test_get_text(filename: str):
    file_path = os.path.join("processed", filename)
    try:
        with open(file_path, "r") as f:
            content = f.read()
        return {"content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File non trovato")

def split_text(text: str, chunk_size: int = CHUNK_SIZE):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")