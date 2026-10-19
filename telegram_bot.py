import json
import time
import urllib.parse
import urllib.request

# Вставь сюда токен своего бота из @BotFather
BOT_TOKEN = "8924657156:AAHD-2YrjjiznnXmXUAD2Dv67dIc4bwscns"
SITE_URL = "https://radarsquad.onrender.com"


def run_bot():
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print(
            "Укажи свой BOT_TOKEN от @BotFather в файле telegram_bot.py для запуска!"
        )
        return

    print("Telegram-бот RadarSquad запущен...")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=20"
            res = json.loads(urllib.request.urlopen(url).read().decode("utf-8"))
            for item in res.get("result", []):
                offset = item["update_id"] + 1
                msg = item.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "")

                if chat_id and text.startswith("/start"):
                    reply = (
                        f"Привет! Это официальный бот RadarSquad.\n\n"
                        f"Твой Telegram Chat ID для уведомлений: {chat_id}\n"
                        f"Скопируй эти цифры и вставь их в окне «Настройки» на сайте: {SITE_URL}"
                    )
                    send_url = (
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    )
                    data = urllib.parse.urlencode(
                        {"chat_id": chat_id, "text": reply}
                    ).encode("utf-8")
                    urllib.request.urlopen(
                        urllib.request.Request(send_url, data=data)
                    )
        except Exception:
            time.sleep(3)


if __name__ == "__main__":
    run_bot()