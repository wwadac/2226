import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Словарь для преобразования символов
FONT_MAP = {
    'a': '𝕒', 'b': '𝕓', 'c': '𝕔', 'd': '𝕕', 'e': '𝕖', 'f': '𝕗', 'g': '𝕘', 'h': '𝕙',
    'i': '𝕚', 'j': '𝕛', 'k': '𝕜', 'l': '𝕝', 'm': '𝕞', 'n': '𝕟', 'o': '𝕠', 'p': '𝕡',
    'q': '𝕢', 'r': '𝕣', 's': '𝕤', 't': '𝕥', 'u': '𝕦', 'v': '𝕧', 'w': '𝕨', 'x': '𝕩',
    'y': '𝕪', 'z': '𝕫', 'A': '𝔸', 'B': '𝔹', 'C': 'ℂ', 'D': '𝔻', 'E': '𝔼', 'F': '𝔽',
    'G': '𝔾', 'H': 'ℍ', 'I': '𝕀', 'J': '𝕁', 'K': '𝕂', 'L': '𝕃', 'M': '𝕄', 'N': 'ℕ',
    'O': '𝕆', 'P': 'ℙ', 'Q': 'ℚ', 'R': 'ℝ', 'S': '𝕊', 'T': '𝕋', 'U': '𝕌', 'V': '𝕍',
    'W': '𝕎', 'X': '𝕏', 'Y': '𝕐', 'Z': 'ℤ'
}

BOLD_FONT_MAP = {
    'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵',
    'i': '𝗶', 'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽',
    'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅',
    'y': '𝘆', 'z': '𝘇', 'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙',
    'G': '𝗚', 'H': '𝗛', 'I': '𝗜', 'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡',
    'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩',
    'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭'
}

SCRIPT_FONT_MAP = {
    'a': '𝒶', 'b': '𝒷', 'c': '𝒸', 'd': '𝒹', 'e': '𝑒', 'f': '𝒻', 'g': '𝑔', 'h': '𝒽',
    'i': '𝒾', 'j': '𝒿', 'k': '𝓀', 'l': '𝓁', 'm': '𝓂', 'n': '𝓃', 'o': '𝑜', 'p': '𝓅',
    'q': '𝓆', 'r': '𝓇', 's': '𝓈', 't': '𝓉', 'u': '𝓊', 'v': '𝓋', 'w': '𝓌', 'x': '𝓍',
    'y': '𝓎', 'z': '𝓏', 'A': '𝒜', 'B': '𝐵', 'C': '𝒞', 'D': '𝒟', 'E': '𝐸', 'F': '𝐹',
    'G': '𝒢', 'H': '𝐻', 'I': '𝐼', 'J': '𝒥', 'K': '𝒦', 'L': '𝐿', 'M': '𝑀', 'N': '𝒩',
    'O': '𝒪', 'P': '𝒫', 'Q': '𝒬', 'R': '𝑅', 'S': '𝒮', 'T': '𝒯', 'U': '𝒰', 'V': '𝒱',
    'W': '𝒲', 'X': '𝒳', 'Y': '𝒴', 'Z': '𝒵'
}

def convert_font(text, font_map):
    """Преобразует текст в указанный шрифт"""
    result = []
    for char in text:
        if char in font_map:
            result.append(font_map[char])
        else:
            result.append(char)
    return ''.join(result)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
🤖 Бот для изменения шрифта текста

Отправьте мне текст, и я преобразую его в разные шрифты!

Доступные команды:
/start - показать это сообщение
/help - помощь
/fonts - показать доступные шрифты

Просто отправьте текст, и получите его в разных стилях!
"""
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📝 Как использовать бота:

1. Просто отправьте любой текст
2. Бот ответит с тем же текстом в разных шрифтах
3. Копируйте понравившийся вариант!

Поддерживаются английские буквы (латиница), цифры и основные символы.
"""
    await update.message.reply_text(help_text)

async def show_fonts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать примеры шрифтов"""
    example_text = "Hello World"
    
    fonts_example = f"""
🎨 Доступные шрифты:

Обычный текст: {example_text}

• 𝕄𝕒𝕥𝕙𝕖𝕞𝕒𝕥𝕚𝕔𝕒𝕝 𝔹𝕠𝕝𝕕: {convert_font(example_text, FONT_MAP)}
• 𝐁𝐨𝐥𝐝: {convert_font(example_text, BOLD_FONT_MAP)}
• 𝒮𝒸𝓇𝒾𝓅𝓉: {convert_font(example_text, SCRIPT_FONT_MAP)}

Отправьте свой текст, чтобы увидеть его во всех стилях!
"""
    await update.message.reply_text(fonts_example)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_text = update.message.text
    
    # Пропускаем команды
    if user_text.startswith('/'):
        return
    
    # Преобразуем текст в разные шрифты
    mathematical = convert_font(user_text, FONT_MAP)
    bold = convert_font(user_text, BOLD_FONT_MAP)
    script = convert_font(user_text, SCRIPT_FONT_MAP)
    
    response = f"""
📝 Ваш текст в разных шрифтах:

𝕄𝕒𝕥𝕙𝕖𝕞𝕒𝕥𝕚𝕔𝕒𝕝 𝔹𝕠𝕝𝕕:
{mathematical}

𝐁𝐨𝐥𝐝:
{bold}

𝒮𝒸𝓇𝒾𝓅𝓉:
{script}

✨ Выберите понравившийся вариант и скопируйте его!
"""
    await update.message.reply_text(response)

def main():
    """Основная функция"""
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота
    TOKEN = '8259782982:AAF_cCRncLPaM2X5KViHg7PF3Vu8lqk1kCA'
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("fonts", show_fonts))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
