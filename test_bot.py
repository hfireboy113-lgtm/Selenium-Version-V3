import requests

from config import BALE_TOKEN
from core.scanner import Scanner
from messenger import send_message

CHAT_ID = 520014214

scanner = Scanner()

try:

    watchlist = scanner.run()

finally:

    scanner.close()

send_message(CHAT_ID, watchlist)