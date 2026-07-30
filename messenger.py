import requests
import time

from config import BALE_TOKEN
from buttons import scan_keyboard

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

MAX_LENGTH = 3500


def send_keyboard(chat_id):

    response = requests.post(
        BASE_URL + "/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "گزینه مورد نظر را انتخاب کنید:",
            "reply_markup": scan_keyboard()
        }
    )

    print("Keyboard Response:")
    print(response.text)


def send_message(chat_id, text):

    parts = []

    while len(text) > MAX_LENGTH:

        cut = text.rfind("\n", 0, MAX_LENGTH)

        if cut == -1:
            cut = MAX_LENGTH

        parts.append(text[:cut])

        text = text[cut:].lstrip()

    parts.append(text)

    for index, part in enumerate(parts, start=1):

        response = requests.post(
            BASE_URL + "/sendMessage",
            json={
                "chat_id": chat_id,
                "text": part
            }
        )

        print(f"\n===== SEND MESSAGE ({index}/{len(parts)}) =====")
        print(f"Chat ID: {chat_id}")
        print("Response:")
        print(response.text)

        time.sleep(0.5)
