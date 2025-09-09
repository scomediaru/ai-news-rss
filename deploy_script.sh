#!/bin/bash

# Скрипт развертывания Dzen News Scraper
# Использование: ./deploy.sh [production|development]

set -e

ENVIRONMENT=${1:-development}
PROJECT_NAME="dzen-news-scraper"

echo "🚀 Развертывание Dzen News Scraper в режиме: $ENVIRONMENT"

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и Docker Compose"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p output logs config

# Создание .env файла если его нет
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cat > .env << EOF
# Основные настройки
MAX_ARTICLES=30
SAVE_FORMAT=both
HEADLESS=true
LOG_LEVEL=INFO

# Настройки задержек
MIN_DELAY=2.0
MAX_DELAY=4.0
ARTICLE_DELAY_MIN=3.0
ARTICLE_DELAY_MAX=6.0

# Директории
OUTPUT_DIR=./output
LOGS_DIR=./logs

# Браузер
BROWSER_TIMEOUT=30000
PAGE_TIMEOUT=20000

# Контент
MAX_CONTENT_LENGTH=5000
MIN_PARAGRAPH_LENGTH=20

# Прокси (при необходимости)
USE_PROXY=false
PROXY_URL=

# Для production
$([ "$ENVIRONMENT" = "production" ] && echo "MAX_ARTICLES=50
ARTICLE_DELAY_MIN=5.0
ARTICLE_DELAY_MAX=10.0")
EOF
fi

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down --remove-orphans || true

# Сборка образов
echo "🏗️  Сборка Docker образов..."
docker-compose build --no-cache

# Запуск в зависимости от окружения
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🌐 Запуск в production режиме..."
    docker-compose up -d
else
    echo "🔧 Запуск в development режиме..."
    docker-compose up -d
fi

# Проверка статуса
echo "⏳ Ожидание запуска контейнеров..."
sleep 10

if docker-compose ps | grep -q "Up"; then
    echo "✅ Контейнеры запущены успешно"
    echo ""
    echo "📊 Статус контейнеров:"
    docker-compose ps
    echo ""
    echo "📝 Логи можно посмотреть командой: docker-compose logs -f"
    echo "📁 Результаты сохраняются в директории: ./output"
    echo "📋 Логи сохраняются в директории: ./logs"
else
    echo "❌ Ошибка при запуске контейнеров"
    echo "Логи:"
    docker-compose logs
    exit 1
fi

echo ""
echo "🎉 Развертывание завершено!"
echo ""
echo "Полезные команды:"
echo "  Просмотр логов:     docker-compose logs -f"
echo "  Остановка:          docker-compose down"
echo "  Перезапуск:         docker-compose restart"
echo "  Ручной запуск:      docker-compose exec dzen-scraper python dzen_scraper.py"