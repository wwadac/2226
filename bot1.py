import telebot
import qrcode
from PIL import Image
import io
import numpy as np

TOKEN = '7795610786:AAHhkUL7WcOLYVO18FDyceG3ZTDtWGpphZo'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        # Конвертируем в изображение PIL
        img = Image.open(io.BytesIO(downloaded))
        
        # Декодируем QR
        from pyzbar.pyzbar import decode
        decoded = decode(img)
        
        if decoded:
            for qr in decoded:
                link = qr.data.decode('utf-8')
                if link.startswith('tg://login'):
                    bot.send_message(message.chat.id, f"✅ Ссылка:\n`{link}`", parse_mode="Markdown")
                    return
            bot.send_message(message.chat.id, f"⚠️ QR не для входа в ТГ:\n`{decoded[0].data.decode('utf-8')}`")
        else:
            bot.send_message(message.chat.id, "❌ QR не найден.")
            
    except ImportError:
        bot.send_message(message.chat.id, "🚫 Ошибка: установи системную библиотеку zbar (libzbar0)")
    except Exception as e:
        bot.send_message(message.chat.id, f"🚫 Ошибка: {e}")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "Отправь QR для входа в ТГ.")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling()
