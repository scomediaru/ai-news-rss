FROM python:3.11-slim

# Установка системных зависимостей
#RUN apt-get update && apt-get install -y \
  #  wget \
   # gnupg \
   # unzip \
   # curl \
   # xvfb \
   # && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    gconf-service \
    libappindicator1 \
    libasound2 \
    libatk1.0-0 \
    libcairo5 \
    libcups2 \
    libfontconfig1 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libicu-dev \
    libjpeg-dev \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpng-dev \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*



# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Установка браузеров Playwright
RUN playwright install chromium
#RUN playwright install chromium   
RUN playwright install-deps chromium

#RUN apt-get update && \
#    (playwright install-deps chromium || true) && \
#    playwright install chromium
    
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
