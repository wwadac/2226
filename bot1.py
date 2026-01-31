import telebot
import subprocess
import tempfile
import os

TOKEN = '7795610786:AAHhkUL7WcOLYVO18FDyceG3ZTDtWGpphZo'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(downloaded)
            tmp_path = tmp.name
        
        result = subprocess.run(['zbarimg', '--quiet', tmp_path], capture_output=True, text=True)
        os.unlink(tmp_path)
        
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line.startswith('QR-Code:'):
                    link = line[8:].strip()
                    if link.startswith('tg://login'):
                        bot.send_message(message.chat.id, f"✅ Ссылка:\n`{link}`", parse_mode="Markdown")
                        return
                    else:
                        bot.send_message(message.chat.id, f"⚠️ Не Telegram логин:\n`{link}`")
                        return
            bot.send_message(message.chat.id, "❌ Не извлеклась ссылка.")
        else:
            bot.send_message(message.chat.id, "❌ QR не найден.")
            
    except FileNotFoundError:
        bot.send_message(message.chat.id, "🚫 Установи zbar-tools: apt-get install zbar-tools")
    except Exception as e:
        bot.send_message(message.chat.id, f"🚫 Ошибка: {e}")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "Отправь фото QR-кода Telegram для входа.")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling()
