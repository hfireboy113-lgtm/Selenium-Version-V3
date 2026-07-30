import time
import requests

from config import BALE_TOKEN
from messenger import send_message, send_keyboard
from core.scanner import Scanner

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

offset = 0
scanning = False


def run_scan(chat_id):
    global scanning

    if scanning:
        send_message(chat_id, "⏳ یک اسکن در حال اجراست. لطفاً منتظر بمانید.")
        return

    scanning = True

    try:
        send_message(chat_id, "⏳ در حال اسکن بازار...")

        scanner = Scanner()

        try:
            output = scanner.run()
        finally:
            scanner.close()

        send_message(chat_id, output)

    except Exception as e:
        print(e)
        send_message(chat_id, f"❌ خطا:\n{e}")

    finally:
        scanning = False


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

                send_keyboard(chat_id)

            elif text == "🔍 اسکن بازار":

                run_scan(chat_id)

        time.sleep(1)

    except Exception as e:

        print(e)

        time.sleep(5)