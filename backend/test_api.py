import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"

def upload_audio():
    files = {"file": ("audio.mp3", open("audio.mp3", "rb"), "audio/mpeg")}
    response = requests.post(f"{BASE_URL}/test_upload_audio", files=files)
    if response.status_code == 200:
        return response.json()["filename"]
    else:
        raise Exception(f"Failed to upload audio: {response.text}")

def get_processed_text(filename):
    response = requests.get(f"{BASE_URL}/test_get_text/{filename}")
    if response.status_code == 200:
        return response.json()["content"]
    else:
        raise Exception(f"Failed to get processed text: {response.text}")

def main():
    try:
        filename = upload_audio()
        print(f"Audio uploaded successfully. Filename: {filename}")

        processed_text = get_processed_text(filename)
        print("Processed text:")
        print(processed_text)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()