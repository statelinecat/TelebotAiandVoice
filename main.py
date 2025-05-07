import io
import json
import time
import threading
import tempfile
import requests
import telebot
import ffmpeg
import speech_recognition as sr
from gtts import gTTS
from dotenv import load_dotenv
import os
import subprocess
import sys

# Добавляем путь к ffmpeg вручную, если не найден
ffmpeg_path = r"C:\ffmpeg\bin"
if ffmpeg_path not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + ffmpeg_path

def check_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        print("❌ ffmpeg не найден. Убедитесь, что ffmpeg установлен и добавлен в переменную окружения PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка при проверке ffmpeg: {e}")
        sys.exit(1)

check_ffmpeg_installed()


def check_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        print("❌ ffmpeg не найден. Убедитесь, что ffmpeg установлен и добавлен в переменную окружения PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка при проверке ffmpeg: {e}")
        sys.exit(1)

# Выполняем проверку перед запуском бота
check_ffmpeg_installed()


# Загружаем переменные из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen/qwen3-4b:free")

bot = telebot.TeleBot(BOT_TOKEN)


class ThinkingIndicator:
    def __init__(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = None

    def start(self):
        msg = self.bot.send_message(self.chat_id, "🐱 Котик думает...")
        self.message_id = msg.message_id

    def stop(self):
        if self.message_id:
            try:
                self.bot.delete_message(self.chat_id, self.message_id)
            except Exception as e:
                print(f"Ошибка при удалении сообщения: {e}")


def generate_with_ai(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return "Не удалось получить ответ от ИИ"
    except Exception as e:
        return f"Ошибка: {str(e)}"


def text_to_speech_elevenlabs(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.3,
            "similarity_boost": 0.75,
            "style": 0.2,
            "speaker_boost": True
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        if response.status_code == 200:
            return io.BytesIO(response.content)
        print(f"Ошибка ElevenLabs: {response.status_code}, {response.text}")
        return None
    except Exception as e:
        print(f"Ошибка ElevenLabs: {e}")
        return None


def text_to_speech_gtts(text):
    try:
        tts = gTTS(text=text, lang='ru')
        voice = io.BytesIO()
        tts.write_to_fp(voice)
        voice.seek(0)
        return voice
    except Exception as e:
        print(f"Ошибка gTTS: {e}")
        return None


def text_to_speech(text):
    voice = text_to_speech_elevenlabs(text)
    if voice is None:
        print("Используем резервный gTTS...")
        voice = text_to_speech_gtts(text)
    return voice


def send_with_voice(chat_id, text, is_command=False):
    bot.send_message(chat_id, text)
    if not is_command and len(text) > 3:
        voice = text_to_speech(text)
        if voice:
            bot.send_voice(chat_id, voice)
            if isinstance(voice, io.BytesIO):
                voice.close()


def voice_to_text(file_path):
    recognizer = sr.Recognizer()
    wav_file = None
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            wav_file = temp_wav.name

        ffmpeg.input(file_path).output(wav_file).run(quiet=True, overwrite_output=True)

        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")
            return text
    except Exception as e:
        print(f"Ошибка при распознавании голоса: {e}")
        return None
    finally:
        if wav_file and os.path.exists(wav_file):
            os.remove(wav_file)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_chat_action(message.chat.id, 'typing')
    time.sleep(1)
    welcome_text = """
Привет! Я умный бот с функциями:
- Отвечаю на приветствия
- Рассказываю анекдоты (/anekdot)
- Могу поддержать беседу
- Отвечаю голосовыми сообщениями

Используй /help для списка команд
"""
    send_with_voice(message.chat.id, welcome_text, is_command=True)


@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
🐱 Доступные команды котика:

/start - Начальное приветствие
/help - Показать это сообщение
/anekdot - Рассказать свежий анекдот

Просто напиши мне что-нибудь, и я постараюсь ответить!
"""
    send_with_voice(message.chat.id, help_text, is_command=True)


@bot.message_handler(commands=['anekdot'])
def tell_joke(message):
    indicator = ThinkingIndicator(bot, message.chat.id)
    indicator.start()
    try:
        prompt = "Расскажи свежий анекдот (только текст, без пояснений)"
        joke = generate_with_ai(prompt)
        send_with_voice(message.chat.id, joke)
    finally:
        indicator.stop()


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if "привет" in message.text.lower():
        bot.send_chat_action(message.chat.id, 'typing')
        time.sleep(1)
        send_with_voice(message.chat.id, "Привет-привет! 😊")
    else:
        indicator = ThinkingIndicator(bot, message.chat.id)
        indicator.start()
        try:
            response = generate_with_ai(message.text)
            send_with_voice(message.chat.id, response)
        finally:
            indicator.stop()


@bot.message_handler(content_types=['voice'])
def handle_voice_message(message):
    indicator = ThinkingIndicator(bot, message.chat.id)
    indicator.start()
    temp_file = "temp_voice.ogg"
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(temp_file, 'wb') as f:
            f.write(downloaded_file)

        text = voice_to_text(temp_file)
        if text:
            bot.send_message(message.chat.id, f"Я услышал: {text}")
            response = generate_with_ai(text)
            send_with_voice(message.chat.id, response)
        else:
            bot.send_message(message.chat.id, "Не удалось распознать голосовое сообщение 😔")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")
    finally:
        indicator.stop()
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
