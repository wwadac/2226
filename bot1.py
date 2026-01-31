import telebot
import requests
from PIL import Image
import io

TOKEN = '7795610786:AAHhkUL7WcOLYVO18FDyceG3ZTDtWGpphZo'
bot = telebot.TeleBot(TOKEN)

def decode_qr_with_api(image_bytes):
    """Используем бесплатный API для декодирования QR"""
    try:
        files = {'file': ('qr.jpg', image_bytes, 'image/jpeg')}
        response = requests.post('https://api.qrserver.com/v1/read-qr-code/', files=files, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and data[0]['symbol'][0]['data']:
                return data[0]['symbol'][0]['data']
    except:
        pass
    return None

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        # Пробуем API
        link = decode_qr_with_api(downloaded)
        
        if link and link.startswith('tg://login'):
            bot.send_message(message.chat.id, f"✅ Ссылка:\n`{link}`", parse_mode="Markdown")
        elif link:
            bot.send_message(message.chat.id, f"⚠️ Не Telegram логин:\n`{link}`", parse_mode="Markdown")
        else:
            # Резервный метод через PIL (ограниченная функциональность)
            try:
                from pyzbar.pyzbar import decode
                img = Image.open(io.BytesIO(downloaded))
                decoded = decode(img)
                if decoded:
                    link2 = decoded[0].data.decode('utf-8')
                    if link2.startswith('tg://login'):
                        bot.send_message(message.chat.id, f"✅ (Pyzbar):\n`{link2}`", parse_mode="Markdown")
                    else:
                        bot.send_message(message.chat.id, f"⚠️ (Pyzbar):\n`{link2}`", parse_mode="Markdown")
                else:
                    bot.send_message(message.chat.id, "❌ QR не найден.")
            except ImportError:
                bot.send_message(message.chat.id, "🚫 Не могу распознать. Установи pyzbar или разреши внешние запросы.")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"🚫 Ошибка: {str(e)}")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "Отправь фото QR-кода Telegram. Используется внешний API для распознавания.")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling()
