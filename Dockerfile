# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Устанавливаем зависимости
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . /app/

# Указываем команду для запуска бота
CMD ["python", "main.py"]
