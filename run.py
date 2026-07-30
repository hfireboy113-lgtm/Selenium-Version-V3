import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

from core.scanner import Scanner
from messenger import send_message


def main():

    chat_id = os.getenv("CHAT_ID")
    channel_chat_id = os.getenv("CHANNEL_CHAT_ID")

    if not chat_id:
        print("CHAT_ID not found")
        return

    scanner = Scanner()

    try:

        print("Scanner started...")

        result = scanner.run()

        send_message(
            chat_id,
            result
        )

        print("Message sent to Bale chat")

        if channel_chat_id:

            send_message(
                channel_chat_id,
                result
            )

            print("Message sent to Bale channel")

    finally:

        scanner.close()


if __name__ == "__main__":
    main()
