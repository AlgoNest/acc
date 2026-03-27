import requests, os
from dotenv import load_dotenv
load_dotenv()

def send_message(phone: str, message: str):
    instance = os.getenv("GREEN_API_INSTANCE")
    token = os.getenv("GREEN_API_TOKEN")
    url = f"https://api.green-api.com/waInstance{instance}/sendMessage/{token}"
    phone_clean = phone.strip().replace("+", "").replace(" ", "")
    payload = {
        "chatId": f"{phone_clean}@c.us",
        "message": message
    }
    r = requests.post(url, json=payload)
    return r.status_code == 200
