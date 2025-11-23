import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from moviepy.editor import *

API_TOKEN = "8259782982:AAF_cCRncLPaM2X5KViHg7PF3Vu8lqk1kCA"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Определяем состояния правильно
class UserStates(StatesGroup):
    waiting_video_circle = State()
    waiting_audio_video = State()
    waiting_gif_video = State()

# Глобальная переменная для хранения качества
user_quality = {}

# Клавиатура основного меню
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎥 Видеокружок", callback_data="video_circle"),
        InlineKeyboardButton("🎵 Аудио MP3", callback_data="extract_audio"),
        InlineKeyboardButton("🔄 GIF", callback_data="create_gif")
    )
    keyboard.add(InlineKeyboardButton("⚙️ Качество", callback_data="quality_settings"))
    return keyboard

# Клавиатура выбора качества
def get_quality_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📱 Низкое (240p)", callback_data="quality_240"),
        InlineKeyboardButton("📱 Среднее (360p)", callback_data="quality_360"),
        InlineKeyboardButton("💻 Высокое (480p)", callback_data="quality_480"),
        InlineKeyboardButton("🖥️ HD (720p)", callback_data="quality_720")
    )
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
    return keyboard

async def start(message: types.Message):
    welcome_text = (
        "🎬 *Видео Бот*\n\n"
        "Я могу:\n"
        "• Создать видеокружок\n" 
        "• Извлечь аудио из видео\n"
        "• Создать GIF анимацию\n"
        "• Изменить качество видео\n\n"
        "Выберите действие:"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

# Обработчик команды start всегда должен работать
async def start_command(message: types.Message):
    await start(message)

async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data
    user_id = callback_query.from_user.id
    
    try:
        if action == "back_to_main":
            await callback_query.message.edit_text(
                "🎬 *Видео Бот*\n\nВыберите действие:",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
        
        elif action == "extract_audio":
            await callback_query.message.edit_text(
                "🎵 Отправьте видео для извлечения аудио (MP3)",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
                )
            )
            await UserStates.waiting_audio_video.set()
        
        elif action == "create_gif":
            await callback_query.message.edit_text(
                "🔄 Отправьте видео для создания GIF\n\n"
                "📝 *Совет:* Короткие видео (до 10 сек) работают лучше",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
                ),
                parse_mode="Markdown"
            )
            await UserStates.waiting_gif_video.set()
        
        elif action == "quality_settings":
            await callback_query.message.edit_text(
                "⚙️ Выберите качество для видеокружка:",
                reply_markup=get_quality_keyboard()
            )
        
        elif action.startswith("quality_"):
            quality = action.split("_")[1]
            quality_map = {"240": 240, "360": 360, "480": 480, "720": 720}
            user_quality[user_id] = quality_map[quality]
            
            await callback_query.message.edit_text(
                f"✅ Качество установлено: {quality}p\n\n"
                "Теперь отправьте видео для создания видеокружка:",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
                )
            )
            await UserStates.waiting_video_circle.set()
        
        elif action == "video_circle":
            await callback_query.message.edit_text(
                "🎥 Отправьте видео для создания видеокружка:",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("⚙️ Качество", callback_data="quality_settings"),
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
                )
            )
            await UserStates.waiting_video_circle.set()
    
    except Exception as e:
        logging.error(f"Ошибка в callback: {e}")
        await callback_query.message.answer("❌ Произошла ошибка. Попробуйте снова.", reply_markup=get_main_keyboard())
    
    await callback_query.answer()

async def process_video_circle(message: types.Message, state: FSMContext):
    try:
        if not message.video:
            await message.answer("Пожалуйста, отправьте видео файл")
            return

        user_id = message.from_user.id
        circle_size = user_quality.get(user_id, 360)  # По умолчанию 360p
        
        # Ограничиваем максимальный размер для видеокружка
        circle_size = min(circle_size, 720)  # Telegram ограничение
        
        await message.answer("🔄 Создаю видеокружок...")
        
        # Скачиваем видео
        video_file_id = message.video.file_id
        file_path = f"temp_video_{user_id}.mp4"
        await message.bot.download_file_by_id(video_file_id, file_path)

        # Обрабатываем видео
        input_video = VideoFileClip(file_path)
        w, h = input_video.size
        
        # Рассчитываем размеры для обрезки
        min_dimension = min(w, h)
        crop_size = min(min_dimension, circle_size)
        
        # Центрируем обрезку
        x_center = w / 2
        y_center = h / 2
        
        output_video = input_video.crop(
            x_center=x_center,
            y_center=y_center,
            width=crop_size,
            height=crop_size
        )
        
        # Ресайзим до нужного размера
        if crop_size != circle_size:
            output_video = output_video.resize((circle_size, circle_size))
        
        output_path = f"output_circle_{user_id}.mp4"
        output_video.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac",
            verbose=False,
            logger=None
        )

        # Отправляем видеокружок
        with open(output_path, "rb") as video:
            await message.bot.send_video_note(
                chat_id=message.chat.id, 
                video_note=video, 
                duration=int(output_video.duration), 
                length=circle_size
            )

        # Очистка
        cleanup_files([file_path, output_path], input_video, output_video)
        await state.finish()
        
        # Возвращаем в главное меню
        await message.answer("✅ Готово! Что дальше?", reply_markup=get_main_keyboard())
        
    except Exception as e:
        logging.error(f"Ошибка создания видеокружка: {e}")
        await message.answer("❌ Ошибка при создании видеокружка. Попробуйте видео меньшего размера.", reply_markup=get_main_keyboard())
        await state.finish()

async def extract_audio_handler(message: types.Message, state: FSMContext):
    try:
        if not message.video:
            await message.answer("Пожалуйста, отправьте видео файл")
            return

        await message.answer("🎵 Извлекаю аудио...")
        
        # Скачиваем видео
        video_file_id = message.video.file_id
        file_path = f"temp_video_{message.from_user.id}.mp4"
        await message.bot.download_file_by_id(video_file_id, file_path)

        # Извлекаем аудио
        video = VideoFileClip(file_path)
        audio_path = f"audio_{message.from_user.id}.mp3"
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)

        # Отправляем аудио
        with open(audio_path, "rb") as audio_file:
            await message.bot.send_audio(
                chat_id=message.chat.id,
                audio=audio_file,
                title="Извлеченное аудио",
                performer="Video Bot"
            )

        # Очистка
        cleanup_files([file_path, audio_path], video)
        await state.finish()
        
        # Возвращаем в главное меню
        await message.answer("✅ Готово! Что дальше?", reply_markup=get_main_keyboard())
        
    except Exception as e:
        logging.error(f"Ошибка извлечения аудио: {e}")
        await message.answer("❌ Ошибка при извлечении аудио", reply_markup=get_main_keyboard())
        await state.finish()

async def create_gif_handler(message: types.Message, state: FSMContext):
    try:
        if not message.video:
            await message.answer("Пожалуйста, отправьте видео файл")
            return

        await message.answer("🔄 Создаю GIF...")
        
        # Скачиваем видео
        video_file_id = message.video.file_id
        file_path = f"temp_video_{message.from_user.id}.mp4"
        await message.bot.download_file_by_id(video_file_id, file_path)

        # Создаем GIF (первые 5 секунд или всю длину если короче)
        video = VideoFileClip(file_path)
        gif_duration = min(5, video.duration)  # Максимум 5 секунд для GIF
        
        # Ресайзим для уменьшения размера
        gif_clip = video.subclip(0, gif_duration).resize(width=320)
        gif_path = f"gif_{message.from_user.id}.gif"
        
        # Сохраняем GIF с оптимизацией
        gif_clip.write_gif(gif_path, program='ffmpeg', fps=8, verbose=False, logger=None)

        # Проверяем размер файла
        file_size = os.path.getsize(gif_path) / (1024 * 1024)  # Размер в MB
        if file_size > 50:  # Если больше 50MB, уменьшаем качество
            gif_clip = video.subclip(0, min(3, video.duration)).resize(width=240)
            gif_clip.write_gif(gif_path, program='ffmpeg', fps=6, verbose=False, logger=None)

        # Отправляем GIF
        with open(gif_path, "rb") as gif_file:
            await message.bot.send_animation(
                chat_id=message.chat.id,
                animation=gif_file,
                caption="Ваш GIF готов! 🎬"
            )

        # Очистка
        cleanup_files([file_path, gif_path], video, gif_clip)
        await state.finish()
        
        # Возвращаем в главное меню
        await message.answer("✅ Готово! Что дальше?", reply_markup=get_main_keyboard())
        
    except Exception as e:
        logging.error(f"Ошибка создания GIF: {e}")
        await message.answer("❌ Ошибка при создании GIF. Попробуйте видео покороче.", reply_markup=get_main_keyboard())
        await state.finish()

def cleanup_files(file_paths, *clips):
    """Очистка временных файлов и закрытие клипов"""
    for clip in clips:
        if clip:
            try:
                clip.close()
            except:
                pass
    
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

# Регистрация хендлеров
dp.register_message_handler(start_command, commands=["start"], state="*")
dp.register_message_handler(start, commands=["start"])
dp.register_callback_query_handler(process_callback, state="*")
dp.register_message_handler(process_video_circle, content_types=types.ContentType.VIDEO, state=UserStates.waiting_video_circle)
dp.register_message_handler(extract_audio_handler, content_types=types.ContentType.VIDEO, state=UserStates.waiting_audio_video)
dp.register_message_handler(create_gif_handler, content_types=types.ContentType.VIDEO, state=UserStates.waiting_gif_video)

# Обработчик для сброса состояния при любом сообщении
async def reset_state_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    await start(message)

dp.register_message_handler(reset_state_handler, commands=["start", "reset"], state="*")

if __name__ == "__main__":
    print("🚀 Бот запущен!")
    executor.start_polling(dp, skip_updates=True)
