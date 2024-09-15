import requests
import os
from dotenv import load_dotenv
from pydub import AudioSegment
import tempfile

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8002"
CHUNK_DURATION_MS = 60000  # 1 minute chunks
OPUS_BITRATE = "32k"  # Adjust this value for desired quality/size trade-off

def convert_and_chunk_audio(audio_path, chunk_duration_ms):
    audio = AudioSegment.from_file(audio_path)
    chunks = []
    for i, chunk in enumerate(audio[::chunk_duration_ms]):
        with tempfile.NamedTemporaryFile(suffix=".opus", delete=False) as temp_file:
            chunk.export(temp_file.name, format="opus", bitrate=OPUS_BITRATE)
            chunks.append(temp_file.name)
    return chunks

def upload_audio_chunk(chunk_path):
    with open(chunk_path, "rb") as audio_file:
        files = {"file": (os.path.basename(chunk_path), audio_file, "audio/opus")}
        response = requests.post(f"{BASE_URL}/test_upload_audio", files=files)
    if response.status_code == 200:
        return response.json()["filename"]
    else:
        raise Exception(f"Failed to upload audio chunk: {response.text}")

def get_processed_text(filename):
    response = requests.get(f"{BASE_URL}/test_get_text/{filename}")
    if response.status_code == 200:
        return response.json()["content"]
    else:
        raise Exception(f"Failed to get processed text: {response.text}")

def main():
    try:
        audio_path = os.path.join(os.path.dirname(__file__), "audio.mp3")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found at {audio_path}")

        chunks = convert_and_chunk_audio(audio_path, CHUNK_DURATION_MS)
        processed_texts = []

        for chunk in chunks:
            filename = upload_audio_chunk(chunk)
            print(f"Chunk uploaded successfully. Filename: {filename}")
            processed_text = get_processed_text(filename)
            processed_texts.append(processed_text)
            os.unlink(chunk)  # Remove temporary chunk file

        final_text = "\n\n".join(processed_texts)
        print("Processed text:")
        print(final_text)

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        print("Please make sure 'audio.mp3' is in the same directory as this script.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()