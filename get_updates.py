import requests

from config import BALE_TOKEN

BASE_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

response = requests.get(BASE_URL + "/getUpdates")

print(response.text)