# Альтернативный Dockerfile на базе Ubuntu для решения проблем с зависимостями
FROM ubuntu:22.04

# Переменные окружения для неинтерактивной установки
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Moscow

# Установка Python и системных зависимостей
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    wget \
    curl \
    unzip \
    xvfb \
    libnss3-dev \
    libatk-bridge2.0-0 \
    libdrm-dev \
    libxkbcommon-dev \
    libgtk-3-dev \
    libgbm-dev \
    libasound2-dev \
    libxss1 \
    libgconf-2-4 \
    libxtst6 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    fonts-ubuntu \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Создание символических ссылок для Python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Обновление pip и установка Python зависимостей
RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

# Установка Playwright браузеров
RUN playwright install chromium
RUN playwright install-deps chromium

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

# Порт для веб-интерфейса (если добавите в будущем)
EXPOSE 8000

# Проверка здоровья контейнера
HEALTHCHECK --interval=30m --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/logs/dzen_scraper.log') else 1)"

# Команда по умолчанию
CMD ["python", "scheduler.py"]