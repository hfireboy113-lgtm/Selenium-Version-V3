import requests
import time

from config import BALE_TOKEN


BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

MAX_LENGTH = 3500


def send_message(chat_id, text):

    parts = []

    while len(text) > MAX_LENGTH:

        cut = text.rfind("\n", 0, MAX_LENGTH)

        if cut == -1:
            cut = MAX_LENGTH

        parts.append(text[:cut])

        text = text[cut:].lstrip()

    parts.append(text)

    for part in parts:

        requests.post(
            BASE_URL + "/sendMessage",
            json={
                "chat_id": chat_id,
                "text": part
            }
        )

        time.sleep(0.5)
