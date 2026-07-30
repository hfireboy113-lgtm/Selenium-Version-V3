import requests

TOKEN = "991504956:orYsZpd4HVNfBxM0MD5XUlrdWEt-dQ5G78A"

url = f"https://tapi.bale.ai/bot{TOKEN}/setWebhook"

response = requests.post(
    url,
    json={
        "url": "https://crypto-scanner-trigger.h-fireboy113.workers.dev/"
    }
)

print(response.text)