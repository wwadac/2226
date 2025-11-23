import os
import logging
import asyncio
import random
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
from telethon.errors import UsernameNotOccupiedError, UsernameInvalidError, UserIdInvalidError
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ===== НАСТРОЙКИ =====
API_ID = 29385016  # твой API ID
API_HASH = "89db2f46dca86b9e7c6f81f2b9f9b3a5"  # твой API HASH
PHONE_NUMBER = "+79044586895"  # твой номер телефона
BOT_TOKEN = "789012345:ABCdefGHIjklMNOpqrsTUVwxyz"  # токен бота от @BotFather

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы для ConversationHandler
WAITING_INPUT = 1

class TelegramProfileChecker:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = None
        
    async def initialize(self):
        self.client = TelegramClient(f'session_{self.phone_number}', self.api_id, self.api_hash)
        await self.client.start(phone=self.phone_number)
        logger.info(f"Telethon клиент запущен для номера: {self.phone_number}")
    
    async def check_by_username(self, username):
        try:
            username = username.lstrip('@')
            user = await self.client.get_entity(username)
            user_full = await self.client(GetFullUserRequest(user))
            
            return {
                'exists': True,
                'user_id': user.id,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'username': user.username or 'Нет username',
                'phone': user.phone or 'Скрыт',
                'bio': user_full.full_user.about or 'Нет био',
                'premium': getattr(user, 'premium', False)
            }
        except UsernameNotOccupiedError:
            return {'exists': False, 'error': 'Пользователь с таким username не найден'}
        except UsernameInvalidError:
            return {'exists': False, 'error': 'Некорректный username'}
        except Exception as e:
            return {'exists': False, 'error': f'Ошибка: {str(e)}'}
    
    async def check_by_user_id(self, user_id):
        try:
            user_id = int(user_id)
            user = await self.client.get_entity(user_id)
            user_full = await self.client(GetFullUserRequest(user))
            
            return {
                'exists': True,
                'user_id': user.id,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'username': user.username or 'Нет username',
                'phone': user.phone or 'Скрыт',
                'bio': user_full.full_user.about or 'Нет био',
                'premium': getattr(user, 'premium', False)
            }
        except UserIdInvalidError:
            return {'exists': False, 'error': 'Пользователь с таким ID не найден'}
        except ValueError:
            return {'exists': False, 'error': 'ID должен быть числом'}
        except Exception as e:
            return {'exists': False, 'error': f'Ошибка: {str(e)}'}
    
    async def check_by_phone(self, phone):
        try:
            phone = ''.join(filter(str.isdigit, phone))
            
            result = await self.client(ImportContactsRequest([
                InputPhoneContact(
                    client_id=random.randint(0, 9999),
                    phone=phone,
                    first_name="Check",
                    last_name="User"
                )
            ]))
            
            if result.users:
                user = result.users[0]
                user_full = await self.client(GetFullUserRequest(user))
                
                return {
                    'exists': True,
                    'user_id': user.id,
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'username': user.username or 'Нет username',
                    'phone': user.phone or 'Скрыт',
                    'bio': user_full.full_user.about or 'Нет био',
                    'premium': getattr(user, 'premium', False)
                }
            else:
                return {'exists': False, 'error': 'Пользователь с таким номером не найден'}
        except Exception as e:
            return {'exists': False, 'error': f'Ошибка при проверке номера: {str(e)}'}

checker = TelegramProfileChecker(API_ID, API_HASH, PHONE_NUMBER)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['🔍 Проверить профиль']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👋 Добро пожаловать в бот для проверки профилей Telegram!\n\n"
        "Я могу проверить существование профиля по:\n"
        "• 📱 Username (например: @username)\n"
        "• 🔢 User ID\n"
        "• 📞 Номеру телефона\n\n"
        "Нажмите '🔍 Проверить профиль' чтобы начать!",
        reply_markup=reply_markup
    )

async def check_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите данные для проверки:\n\n"
        "📱 Username: @username или username\n"
        "🔢 User ID: 123456789\n"
        "📞 Номер телефона: +79991234567\n\n"
        "Или отправьте /cancel для отмены"
    )
    return WAITING_INPUT

async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    
    await update.message.reply_text("🔍 Проверяю...")
    
    if user_input.startswith('@') or (not user_input.isdigit() and not any(c in user_input for c in '+ -()')):
        result = await checker.check_by_username(user_input)
    elif user_input.isdigit():
        result = await checker.check_by_user_id(user_input)
    else:
        result = await checker.check_by_phone(user_input)
    
    if result['exists']:
        premium_emoji = "⭐" if result['premium'] else "⚪"
        response = (
            f"✅ Профиль найден!\n\n"
            f"🆔 ID: {result['user_id']}\n"
            f"👤 Имя: {result['first_name']}\n"
            f"📛 Фамилия: {result['last_name']}\n"
            f"📱 Username: @{result['username']}\n"
            f"📞 Телефон: {result['phone']}\n"
            f"📝 Био: {result['bio']}\n"
            f"{premium_emoji} Премиум: {'Да' if result['premium'] else 'Нет'}"
        )
    else:
        response = f"❌ {result['error']}"
    
    await update.message.reply_text(response)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🔍 Проверить профиль$'), check_profile)],
        states={WAITING_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_input)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    print("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    # Замени эти значения на свои:
    # API_ID - получи на https://my.telegram.org/apps
    # API_HASH - получи на https://my.telegram.org/apps  
    # PHONE_NUMBER - твой номер в формате +79991234567
    # BOT_TOKEN - получи у @BotFather в Telegram
    
    asyncio.get_event_loop().run_until_complete(checker.initialize())
    main()
