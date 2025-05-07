# Voice Chat Telegram Bot 🎤

Умный Telegram-бот с поддержкой:
- Голосовых сообщений (распознавание и генерация)
- AI-ответов через OpenRouter
- Синтеза речи с ElevenLabs/gTTS

## Как запустить локально

```bash
git clone https://github.com/yourname/voice-chat-bot.git
cd voice-chat-bot
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
cp .env.example .env  # Заполни своими ключами
python bot.py
