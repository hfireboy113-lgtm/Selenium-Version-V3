import time
import requests

from config import BALE_TOKEN
from messenger import send_message, send_keyboard


BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

offset = 0


while True:

    try:

        response = requests.get(
            BASE_URL + "/getUpdates",
            params={
                "offset": offset,
                "timeout": 20
            },
            timeout=30
        ).json()

        if not response["ok"]:
            time.sleep(2)
            continue

        for update in response["result"]:

            offset = update["update_id"] + 1

            if "message" not in update:
                continue

            message = update["message"]

            if "text" not in message:
                continue

            chat_id = message["chat"]["id"]
            text = message["text"]

            if text == "/start":

                send_message(
                    chat_id,
                    "✅ ربات فعال است.\n"
                    "اسکن بازار به صورت خودکار هر ۴ ساعت انجام می‌شود."
                )

        time.sleep(1)

    except Exception as e:

        print(e)

        time.sleep(5)
