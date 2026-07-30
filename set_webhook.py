import requests

TOKEN = "توکن_بله"

url = f"https://tapi.bale.ai/bot{TOKEN}/setWebhook"

response = requests.post(
    url,
    json={
        "url": "https://crypto-scanner-trigger.h-fireboy113.workers.dev/"
    }
)

print(response.text)
