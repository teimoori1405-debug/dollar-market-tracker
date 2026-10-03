import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("EITAA_TOKEN")
CHAT_ID = os.getenv("EITAA_CHAT_ID")

def send_message(text):
    url = f"https://eitaayar.ir/api/{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=data, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

send_message("Test with new token!")
