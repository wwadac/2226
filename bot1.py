import telebot
import cv2
import os

TOKEN = '7795610786:AAHhkUL7WcOLYVO18FDyceG3ZTDtWGpphZo'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)

        with open('qr.jpg', 'wb') as f:
            f.write(downloaded)

        img = cv2.imread('qr.jpg')
        detector = cv2.QRCodeDetector()
        link, _, _ = detector.detectAndDecode(img)

        os.remove('qr.jpg')

        if link:
            bot.send_message(message.chat.id, f'Ссылка: {link}')
        else:
            bot.send_message(message.chat.id, 'QR не распознан.')

    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка: {e}')

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, 'Отправь фото QR-кода.')

bot.polling()
