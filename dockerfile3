FROM python:3.11-slim

# Установка системных зависимостей (оптимизированная версия)
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    xvfb \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    libxss1 \
    libgconf-2-4 \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-unifont \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Установка Chromium для Playwright
RUN playwright install chromium

# Копирование исходного кода
COPY . .

# Создание директорий для данных
RUN mkdir -p /app/output /app/logs

# Создание пользователя для безопасности
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app
USER scraper

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HEADLESS=true
ENV OUTPUT_DIR=/app/output
ENV LOGS_DIR=/app/logs

# Порт для веб-интерфейса
EXPOSE 8000

# Проверка здоровья контейнера
HEALTHCHECK --interval=30m --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/logs/dzen_scraper.log') else 1)"

# Команда по умолчанию
CMD ["python", "scheduler.py"]
