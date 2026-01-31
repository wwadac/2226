import telebot
import cv2
import os
import numpy as np

TOKEN = '7795610786:AAHhkUL7WcOLYVO18FDyceG3ZTDtWGpphZo'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)

        img_array = np.frombuffer(downloaded, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            bot.send_message(message.chat.id, "❌ Не удалось прочитать изображение.")
            return

        detector = cv2.QRCodeDetector()
        link, _, _ = detector.detectAndDecode(img)

        if link and link.startswith('tg://login'):
            bot.send_message(message.chat.id, f"✅ Успешно!\n`{link}`", parse_mode="Markdown")
        elif link:
            bot.send_message(message.chat.id, f"⚠️ Распознано, но это не Telegram логин:\n`{link}`", parse_mode="Markdown")
        else:
            # Пробуем улучшить контраст и переделкать
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
            link2, _, _ = detector.detectAndDecode(thresh)
            if link2 and link2.startswith('tg://login'):
                bot.send_message(message.chat.id, f"✅ Успешно (после обработки)!\n`{link2}`", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, "❌ Не удалось распознать Telegram QR-код. Убедись, что фото чёткое и не искажено.")

    except Exception as e:
        bot.send_message(message.chat.id, f"🚫 Ошибка: {str(e)}")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "Отправь мне фото QR-кода для входа в Telegram (tg://login).")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling()
