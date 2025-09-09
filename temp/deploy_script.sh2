#!/bin/bash

# Исправленный скрипт развертывания Dzen News Scraper
# Автоматически определяет лучший Docker образ для системы

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

# Определение версии OS для выбора подходящего Dockerfile
OS_ID=$(grep '^ID=' /etc/os-release | cut -d'=' -f2 | tr -d '"')
OS_VERSION=$(grep '^VERSION_ID=' /etc/os-release | cut -d'=' -f2 | tr -d '"')

echo "🔍 Определена система: $OS_ID $OS_VERSION"

# Создание docker-compose.yml с правильным Dockerfile
cat > docker-compose.yml << EOF
version: '3.8'

services:
  dzen-scraper:
    build:
      context: .
      dockerfile: $(if [[ "$OS_ID" == "debian" && "$OS_VERSION" > "11" ]] || [[ "$OS_ID" == "ubuntu" ]]; then echo "Dockerfile.ubuntu"; else echo "Dockerfile"; fi)
    container_name: dzen-news-scraper
    restart: unless-stopped
    environment:
      - HEADLESS=true
      - MAX_ARTICLES=${MAX_ARTICLES:-30}
      - SAVE_FORMAT=${SAVE_FORMAT:-both}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - MIN_DELAY=${MIN_DELAY:-2.0}
      - MAX_DELAY=${MAX_DELAY:-4.0}
      - ARTICLE_DELAY_MIN=${ARTICLE_DELAY_MIN:-3.0}
      - ARTICLE_DELAY_MAX=${ARTICLE_DELAY_MAX:-6.0}
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
      - ./config:/app/config
    deploy:
      resources:
        limits:
          memory: 3G
          cpus: '1.5'
        reservations:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "python", "-c", "import os; exit(0 if os.path.exists('/app/logs/dzen_scraper.log') else 1)"]
      interval: 30m
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  scraper_data:
  scraper_logs:
EOF

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p output logs config

# Загрузка переменных из .env если файл существует
if [ -f .env ]; then
    echo "📝 Загрузка переменных из .env..."
    export $(grep -v '^#' .env | xargs)
fi

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

# Функция проверки успешности сборки
check_build() {
    if docker images | grep -q "${PROJECT_NAME}"; then
        echo "✅ Образ собран успешно"
        return 0
    else
        echo "❌ Ошибка сборки образа"
        return 1
    fi
}

# Функция сборки с fallback на альтернативный образ
build_with_fallback() {
    local dockerfile=$1
    echo "🏗️  Попытка сборки с $dockerfile..."
    
    if docker-compose build --no-cache; then
        echo "✅ Сборка успешна с $dockerfile"
        return 0
    else
        echo "⚠️  Ошибка сборки с $dockerfile"
        return 1
    fi
}

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down --remove-orphans || true

# Очистка старых образов
echo "🧹 Очистка старых образов..."
docker system prune -f || true

# Попытка сборки образов
echo "🏗️  Сборка Docker образов..."

# Сначала пробуем с автоматически выбранным Dockerfile
if ! build_with_fallback "auto"; then
    echo "⚠️  Первая попытка не удалась, пробуем Ubuntu образ..."
    
    # Принудительно используем Ubuntu Dockerfile
    sed -i 's/dockerfile: .*/dockerfile: Dockerfile.ubuntu/' docker-compose.yml
    
    if ! build_with_fallback "Dockerfile.ubuntu"; then
        echo "⚠️  Вторая попытка не удалась, пробуем базовый Dockerfile..."
        
        # Используем базовый Dockerfile с игнорированием ошибок зависимостей
        sed -i 's/dockerfile: .*/dockerfile: Dockerfile/' docker-compose.yml
        
        if ! build_with_fallback "Dockerfile"; then
            echo "❌ Все попытки сборки неудачны"
            echo "Попробуйте:"
            echo "1. Обновить Docker: sudo apt update && sudo apt upgrade docker.io"
            echo "2. Увеличить память для Docker"
            echo "3. Проверить интернет-соединение"
            exit 1
        fi
    fi
fi

# Запуск в зависимости от окружения
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🌐 Запуск в production режиме..."
    docker-compose up -d
else
    echo "🔧 Запуск в development режиме..."
    docker-compose up -d
fi

# Ожидание запуска
echo "⏳ Ожидание запуска контейнеров..."
sleep 15

# Проверка статуса с несколькими попытками
for i in {1..5}; do
    echo "🔍 Проверка статуса (попытка $i/5)..."
    
    if docker-compose ps | grep -q "Up"; then
        echo "✅ Контейнеры запущены успешно"
        echo ""
        echo "📊 Статус контейнеров:"
        docker-compose ps
        echo ""
        echo "📝 Просмотр логов: docker-compose logs -f"
        echo "📁 Результаты: ./output"
        echo "📋 Логи: ./logs"
        echo "🔧 Ручной запуск: docker-compose exec dzen-scraper python dzen_scraper.py"
        echo ""
        echo "🎉 Развертывание завершено!"
        exit 0
    fi
    
    if [ $i -eq 5 ]; then
        echo "❌ Контейнеры не запустились после 5 попыток"
        echo ""
        echo "📋 Логи для диагностики:"
        docker-compose logs --tail=50
        echo ""
        echo "🔧 Попробуйте:"
        echo "  docker-compose down"
        echo "  docker system prune -a"
        echo "  ./deploy_fixed.sh"
        exit 1
    fi
    
    sleep 10
done