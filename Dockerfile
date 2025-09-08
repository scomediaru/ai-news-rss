FROM python:3.11-slim

# Установка системных зависимостей
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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


