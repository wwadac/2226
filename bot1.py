import logging
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telethon import TelegramClient, functions
from telethon.sessions import StringSession
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8259782982:AAF_cCRncLPaM2X5KViHg7PF3Vu8lqk1kCA"
API_ID = "29385016"  # Получить на my.telegram.org
API_HASH = "3c57df8805ab5de5a23a032ed39b9af9"  # Получить на my.telegram.org

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_sessions (
            session_name TEXT PRIMARY KEY,
            string_session TEXT,
            phone_number TEXT,
            is_active BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Глобальные переменные
active_clients = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        "Я бот для управления Telegram аккаунтами через сессии.\n\n"
        "Доступные команды:\n"
        "/add_session - Добавить сессию Telethon\n"
        "/send_message - Отправить сообщение через сессию\n"
        "/change_name - Изменить имя через сессию\n"
        "/list_sessions - Список активных сессий\n"
        "/logout_session - Выйти из сессии"
    )

# Добавление Telethon сессии
async def add_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Использование: /add_session <session_name> <phone_number>\n\n"
            "Пример: /add_session my_session +79123456789\n\n"
            "После ввода команды бот запросит код авторизации."
        )
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Нужно указать название сессии и номер телефона")
        return
    
    session_name = context.args[0]
    phone_number = context.args[1]
    
    # Сохраняем информацию для следующего шага
    context.user_data['awaiting_code'] = True
    context.user_data['session_name'] = session_name
    context.user_data['phone_number'] = phone_number
    
    try:
        # Создаем клиент Telethon
        client = TelegramClient(
            StringSession(), 
            int(API_ID), 
            API_HASH
        )
        
        await client.connect()
        
        # Отправляем код
        sent_code = await client.send_code_request(phone_number)
        context.user_data['phone_code_hash'] = sent_code.phone_code_hash
        context.user_data['client'] = client
        
        await update.message.reply_text(
            f"📱 Код отправлен на номер {phone_number}.\n"
            f"Введите код в формате: /code <код>"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

# Обработка кода авторизации
async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_code'):
        await update.message.reply_text("Сначала используйте /add_session")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /code <код_из_смс>")
        return
    
    code = context.args[0].strip()
    client = context.user_data.get('client')
    session_name = context.user_data.get('session_name')
    phone_number = context.user_data.get('phone_number')
    phone_code_hash = context.user_data.get('phone_code_hash')
    
    try:
        # Авторизуем клиента
        await client.sign_in(
            phone=phone_number,
            code=code,
            phone_code_hash=phone_code_hash
        )
        
        # Сохраняем строку сессии в базу
        string_session = client.session.save()
        
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO telegram_sessions 
            (session_name, string_session, phone_number, is_active) 
            VALUES (?, ?, ?, ?)
        ''', (session_name, string_session, phone_number, True))
        conn.commit()
        conn.close()
        
        # Сохраняем активного клиента
        active_clients[session_name] = client
        
        # Очищаем временные данные
        context.user_data.clear()
        
        await update.message.reply_text(
            f"✅ Сессия '{session_name}' успешно авторизована!\n"
            f"Теперь вы можете использовать эту сессию для отправки сообщений."
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка авторизации: {str(e)}")

# Отправка сообщения через сессию
async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Использование: /send_message <session_name> <username/phone> <message>\n\n"
            "Пример: /send_message my_session @username Привет как дела?"
        )
        return
    
    session_name = context.args[0]
    target = context.args[1]
    message = ' '.join(context.args[2:])
    
    if session_name not in active_clients:
        await update.message.reply_text(f"❌ Сессия '{session_name}' не найдена. Сначала добавьте сессию через /add_session")
        return
    
    client = active_clients[session_name]
    
    try:
        # Отправляем сообщение
        await client.send_message(target, message)
        await update.message.reply_text(f"✅ Сообщение отправлено через сессию '{session_name}'")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка отправки: {str(e)}")

# Изменение имени через сессию
async def change_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Использование: /change_name <session_name> <first_name> <last_name>\n\n"
            "Пример: /change_name my_session Иван Иванов"
        )
        return
    
    session_name = context.args[0]
    first_name = context.args[1]
    last_name = ' '.join(context.args[2:])
    
    if session_name not in active_clients:
        await update.message.reply_text(f"❌ Сессия '{session_name}' не найдена.")
        return
    
    client = active_clients[session_name]
    
    try:
        # Меняем имя профиля
        await client(functions.account.UpdateProfileRequest(
            first_name=first_name,
            last_name=last_name
        ))
        
        await update.message.reply_text(
            f"✅ Имя профиля изменено через сессию '{session_name}'\n"
            f"Новое имя: {first_name} {last_name}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка изменения имени: {str(e)}")

# Список активных сессий
async def list_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT session_name, phone_number, is_active FROM telegram_sessions')
    sessions = cursor.fetchall()
    conn.close()
    
    if not sessions:
        await update.message.reply_text("📭 Нет активных сессий.")
        return
    
    sessions_text = "📱 Активные сессии:\n\n"
    for session in sessions:
        status = "✅ Активна" if session[2] else "❌ Неактивна"
        is_loaded = "🟢 В памяти" if session[0] in active_clients else "⚪ Не в памяти"
        sessions_text += f"Имя: {session[0]}\nТелефон: {session[1]}\nСтатус: {status}\n{is_loaded}\n\n"
    
    await update.message.reply_text(sessions_text)

# Выход из сессии
async def logout_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /logout_session <session_name>")
        return
    
    session_name = context.args[0]
    
    if session_name in active_clients:
        client = active_clients[session_name]
        await client.log_out()
        await client.disconnect()
        del active_clients[session_name]
    
    # Обновляем базу данных
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM telegram_sessions WHERE session_name = ?', (session_name,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Сессия '{session_name}' завершена.")

# Загрузка сессий при старте
async def load_sessions():
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT session_name, string_session FROM telegram_sessions WHERE is_active = 1')
    sessions = cursor.fetchall()
    conn.close()
    
    for session_name, string_session in sessions:
        try:
            client = TelegramClient(
                StringSession(string_session), 
                int(API_ID), 
                API_HASH
            )
            await client.connect()
            
            if await client.is_user_authorized():
                active_clients[session_name] = client
                logger.info(f"✅ Сессия '{session_name}' загружена")
            else:
                logger.warning(f"❌ Сессия '{session_name}' не авторизована")
                
        except Exception as e:
            logger.error(f"⚠️ Ошибка загрузки сессии '{session_name}': {e}")

# Основная асинхронная функция
async def main():
    # Загружаем сессии при старте
    await load_sessions()
    
    # Создаем приложение бота
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_session", add_session))
    application.add_handler(CommandHandler("code", handle_code))
    application.add_handler(CommandHandler("send_message", send_message))
    application.add_handler(CommandHandler("change_name", change_name))
    application.add_handler(CommandHandler("list_sessions", list_sessions))
    application.add_handler(CommandHandler("logout_session", logout_session))
    
    # Запускаем бота
    print("🤖 Бот запущен...")
    await application.run_polling()

if __name__ == '__main__':
    # Запускаем асинхронную основную функцию
    asyncio.run(main())
