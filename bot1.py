import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from moviepy.editor import *
from PIL import Image

API_TOKEN = "8324933170:AAFatQ1T42ZJ70oeWS2UJkcXFeiwUFCIXAk"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния для FSM
class UserState(FSMContext):
    pass

# Клавиатура основного меню
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎥 Видеокружок", callback_data="video_circle"),
        InlineKeyboardButton("🎵 Аудио MP3", callback_data="extract_audio"),
        InlineKeyboardButton("🔄 GIF", callback_data="create_gif"),
        InlineKeyboardButton("⚙️ Качество", callback_data="quality_settings")
    )
    return keyboard

# Клавиатура выбора качества
def get_quality_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📱 Низкое (240p)", callback_data="quality_240"),
        InlineKeyboardButton("📱 Среднее (360p)", callback_data="quality_360"),
        InlineKeyboardButton("💻 Высокое (480p)", callback_data="quality_480"),
        InlineKeyboardButton("🖥️ HD (720p)", callback_data="quality_720"),
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    )
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

async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data
    
    if action == "back_to_main":
        await callback_query.message.edit_reply_markup(reply_markup=get_main_keyboard())
    
    elif action == "extract_audio":
        await callback_query.message.edit_text(
            "🎵 Отправьте видео для извлечения аудио (MP3)",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
            )
        )
        await state.set_state("waiting_audio_video")
    
    elif action == "create_gif":
        await callback_query.message.edit_text(
            "🔄 Отправьте видео для создания GIF\n\n"
            "📝 *Совет:* Короткие видео (до 10 сек) работают лучше",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
            ),
            parse_mode="Markdown"
        )
        await state.set_state("waiting_gif_video")
    
    elif action == "quality_settings":
        await callback_query.message.edit_text(
            "⚙️ Выберите качество для видеокружка:",
            reply_markup=get_quality_keyboard()
        )
    
    elif action.startswith("quality_"):
        quality = action.split("_")[1]
        quality_map = {"240": 240, "360": 360, "480": 480, "720": 720}
        await state.update_data(quality=quality_map[quality])
        await callback_query.message.edit_text(
            f"✅ Качество установлено: {quality}p\n\n"
            "Теперь отправьте видео для создания видеокружка:",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
            )
        )
        await state.set_state("waiting_video_circle")
    
    elif action == "video_circle":
        await callback_query.message.edit_text(
            "🎥 Отправьте видео для создания видеокружка:",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("⚙️ Качество", callback_data="quality_settings"),
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
            )
        )
        await state.set_state("waiting_video_circle")
    
    await callback_query.answer()

async def process_video_circle(message: types.Message, state: FSMContext):
    try:
        if not message.video:
            await message.answer("Пожалуйста, отправьте видео файл")
            return

        user_data = await state.get_data()
        circle_size = user_data.get('quality', 360)  # По умолчанию 360p
        
        await message.answer("🔄 Создаю видеокружок...")
        
        # Скачиваем видео
        video_file_id = message.video.file_id
        file_path = f"temp_video_{message.from_user.id}.mp4"
        await message.bot.download_file_by_id(video_file_id, file_path)

        # Обрабатываем видео
        input_video = VideoFileClip(file_path)
        w, h = input_video.size
        aspect_ratio = float(w) / float(h)
        
        if w > h:
            new_w = int(circle_size * aspect_ratio)
            new_h = circle_size
        else:
            new_w = circle_size
            new_h = int(circle_size / aspect_ratio)
            
        resized_video = input_video.resize((new_w, new_h))
        output_video = resized_video.crop(
            x_center=resized_video.w/2, 
            y_center=resized_video.h/2, 
            width=circle_size, 
            height=circle_size
        )
        
        output_path = f"output_circle_{message.from_user.id}.mp4"
        output_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

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
        
    except Exception as e:
        logging.error(f"Ошибка создания видеокружка: {e}")
        await message.answer("❌ Ошибка при создании видеокружка")

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
        video.audio.write_audiofile(audio_path)

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
        
    except Exception as e:
        logging.error(f"Ошибка извлечения аудио: {e}")
        await message.answer("❌ Ошибка при извлечении аудио")

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
        gif_clip.write_gif(gif_path, program='ffmpeg', fps=10)

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
        
    except Exception as e:
        logging.error(f"Ошибка создания GIF: {e}")
        await message.answer("❌ Ошибка при создании GIF")

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
dp.register_message_handler(start, commands=["start"])
dp.register_callback_query_handler(process_callback, state="*")
dp.register_message_handler(process_video_circle, content_types=types.ContentType.VIDEO, state="waiting_video_circle")
dp.register_message_handler(extract_audio_handler, content_types=types.ContentType.VIDEO, state="waiting_audio_video")
dp.register_message_handler(create_gif_handler, content_types=types.ContentType.VIDEO, state="waiting_gif_video")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
