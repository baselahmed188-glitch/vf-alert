import os
import re
import json
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://eshop.vodafone.com.eg/ar/lines/red/numbers"

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

STATE_FILE = Path("seen_numbers.json")


def send_telegram(message):
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

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)

    if not result.get("ok"):
        raise RuntimeError("Telegram message failed")


def get_numbers():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        try:
            page = browser.new_page(locale="ar-EG")
            page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=60000
            )
            page.wait_for_timeout(15000)

            text = page.locator("body").inner_text()

            if "connection failed" in text.lower():
                raise RuntimeError("Vodafone connection failed")

            matches = re.findall(
                r"(?<!\d)(?:\+?20|0)?1[0125](?:[\s-]?\d){8}(?!\d)",
                text
            )

            numbers = set()

            for match in matches:
                number = re.sub(r"\D", "", match)

                if number.startswith("20"):
                    number = "0" + number[2:]

                if len(number) == 10 and number.startswith("1"):
                    number = "0" + number

                if len(number) == 11 and "00" in number:
                    numbers.add(number)

            return numbers

        finally:
            browser.close()


def main():
    numbers = get_numbers()

    if not numbers:
        print("No matching numbers found. State unchanged.")
        return

    if STATE_FILE.exists():
        previous = set(json.loads(STATE_FILE.read_text()))
    else:
        previous = set()

    new_numbers = numbers - previous

    if not STATE_FILE.exists():
        print("First scan: baseline created.")
    else:
        for number in sorted(new_numbers):
            send_telegram(
                f"Vodafone RED Alert\n"
                f"New number containing 00:\n{number}"
            )
            print("Alert sent:", number)

    updated = previous | numbers

    STATE_FILE.write_text(
        json.dumps(sorted(updated), indent=2)
    )

    print("Matching numbers:", len(numbers))
    print("New numbers:", len(new_numbers))


if __name__ == "__main__":
    main()
