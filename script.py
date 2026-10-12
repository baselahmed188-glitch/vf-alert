import os
import json
import urllib.request

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

message = "✅ Vodafone RED Alert is working!"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

data = json.dumps({
    "chat_id": CHAT_ID,
    "text": message
}).encode("utf-8")

request = urllib.request.Request(
    url,
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(request, timeout=20) as response:
    result = json.load(response)

if result.get("ok"):
    print("Telegram message sent successfully!")
else:
    print("Telegram message failed.")
