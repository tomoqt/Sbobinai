from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import openai

# Load environment variables
load_dotenv()

# Initialize OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Environment variables
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o-mini")

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
    
    with open(file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe(WHISPER_MODEL, audio_file)
    
    # Clean up temporary file
    os.remove(file_path)
    
    response = openai.ChatCompletion.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": "Sei un assistente utile che struttura il testo in un formato markdown leggibile."},
            {"role": "user", "content": f"Per favore, struttura questo testo in un formato markdown leggibile, mantenendo il contenuto estremamente fedele all'originale: {transcript['text']}"}
        ]
    )
    final_text = response.choices[0].message['content']
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")