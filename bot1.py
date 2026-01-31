import telebot
from pyzbar.pyzbar import decode
import numpy as np
import cv2

TOKEN = '7795610786:AAHhkUL7WcOLYVO18FDyceG3ZTDtWGpphZo'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)

        img_array = np.frombuffer(downloaded, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)

        if img is None:
            bot.send_message(message.chat.id, "❌ Не читается.")
            return

        decoded = decode(img)
        if decoded:
            for qr in decoded:
                link = qr.data.decode('utf-8')
                if link.startswith('tg://login'):
                    bot.send_message(message.chat.id, f"✅ Ссылка:\n`{link}`", parse_mode="Markdown")
                    return
            bot.send_message(message.chat.id, f"⚠️ QR найден, но не логин ТГ:\n`{decoded[0].data.decode('utf-8')}`")
        else:
            bot.send_message(message.chat.id, "❌ QR не найден.")

    except Exception as e:
        bot.send_message(message.chat.id, f"🚫 Ошибка: {e}")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "Отправь QR для входа в ТГ.")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling()
