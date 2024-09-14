from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import BaseModel
from typing import Optional
import requests
import openai
import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = FastAPI()

# Environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o-mini")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))

openai.api_key = OPENAI_API_KEY

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://oauth2.googleapis.com/token",
)

class User(BaseModel):
    email: str

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        idinfo = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        return User(email=idinfo['email'])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali di autenticazione non valide",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...), user: User = Depends(verify_token)):
    # Save the uploaded file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Use Whisper API to transcribe audio
    with open(file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe(WHISPER_MODEL, audio_file)
    
    # Process transcript with GPT-4o-mini
    chunks = split_text(transcript['text'], CHUNK_SIZE)
    processed_chunks = []
    for chunk in chunks:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "Sei un assistente utile che struttura il testo in un formato markdown leggibile.Mantieni il testo estremamente simile a quello presente, ma eliminado elementi colloquiali e rendendo il discorso un testo coerente e pulito."},
                {"role": "user", "content": f"Per favore, struttura questo testo in un formato markdown leggibile, mantenendo il contenuto estremamente fedele all'originale: {chunk}"}
            ]
        )
        processed_chunks.append(response.choices[0].message['content'])
    
    final_text = "\n\n".join(processed_chunks)
    
    # Save processed text
    with open(f"processed/{file.filename}.md", "w") as f:
        f.write(final_text)
    
    return {"message": "Audio elaborato con successo", "filename": f"{file.filename}.md"}

@app.get("/get_text/{filename}")
async def get_text(filename: str, user: User = Depends(verify_token)):
    try:
        with open(f"processed/{filename}", "r") as f:
            content = f.read()
        return {"content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File non trovato")

def split_text(text: str, chunk_size: int = CHUNK_SIZE):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

@app.get("/login/google")
async def login_google():
    return {
        "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    }

@app.get("/auth/google")
async def auth_google(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data)
    return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)