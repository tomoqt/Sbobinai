import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8002"

def upload_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        files = {"file": (os.path.basename(audio_path), audio_file, "audio/mp3")}
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
        audio_path = os.path.join(os.path.dirname(__file__), "audio.mp3")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found at {audio_path}")

        filename = upload_audio(audio_path)
        print(f"Audio uploaded successfully. Filename: {filename}")
        processed_text = get_processed_text(filename)
        print("Processed text:")
        print(processed_text)

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        print("Please make sure 'audio.mp3' is in the same directory as this script.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()