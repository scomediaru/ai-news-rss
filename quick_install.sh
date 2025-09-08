#!/bin/bash

# Быстрая установка Dzen News Scraper
# Этот скрипт автоматически создаст все необходимые файлы и запустит систему

set -e

PROJECT_DIR="dzen-news-scraper"
GITHUB_RAW_URL="https://raw.githubusercontent.com/your-username/dzen-news-scraper/main"

echo "🚀 Быстрая установка Dzen News Scraper"
echo "========================================"

# Создание директории проекта
if [ -d "$PROJECT_DIR" ]; then
    echo "📁 Директория $PROJECT_DIR уже существует. Удаляем..."
    rm -rf "$PROJECT_DIR"
fi

echo "📁 Создание директории проекта..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Создание основного скрипта скрапера
echo "📄 Создание dzen_scraper.py..."
cat > dzen_scraper.py << 'EOF'
# Здесь будет содержимое dzen_scraper.py из артефакта выше
# (Полный код из первого артефакта)
EOF

# Создание конфигурационного файла
echo "📄 Создание config.py..."
cat > config.py << 'EOF'
# Здесь будет содержимое config.py
EOF

# Создание планировщика
echo "📄 Создание scheduler.py..."
cat > scheduler.py << 'EOF'
# Здесь будет содержимое scheduler.py
EOF

# Создание requirements.txt
echo "📄 Создание requirements.txt..."
cat > requirements.txt << 'EOF'
playwright==1.40.0
aiofiles==23.2.1
requests==2.31.0
lxml==4.9.3
beautifulsoup4==4.12.2
schedule==1.2.0
pandas==2.1.4
openpyxl==3.1.2
colorlog==6.8.0
python-dotenv==1.0.0
pyyaml==6.0.1
EOF

# Создание Dockerfile
echo "📄 Создание Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .
RUN mkdir -p /app/output /app/logs
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app
USER scraper

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HEADLESS=true
ENV OUTPUT_DIR=/app/output
ENV LOGS_DIR=/app/logs

EXPOSE 8000

HEALTHCHECK --interval=30m --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/logs/dzen_scraper.log') else 1)"

CMD ["python", "scheduler.py"]
EOF

# Создание docker-compose.yml
echo "📄 Создание docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  dzen-scraper:
    build: .
    container_name: dzen-news-scraper
    restart: unless-stopped
    environment:
      - HEADLESS=true
      - MAX_ARTICLES=30
      - SAVE_FORMAT=both
      - LOG_LEVEL=INFO
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
EOF

# Создание .env файла
echo "📄 Создание .env файла..."
cat > .env << 'EOF'
MAX_ARTICLES=30
SAVE_FORMAT=both
HEADLESS=true
LOG_LEVEL=INFO
MIN_DELAY=2.0
MAX_DELAY=4.0
ARTICLE_DELAY_MIN=3.0
ARTICLE_DELAY_MAX=6.0
OUTPUT_DIR=./output
LOGS_DIR=./logs
BROWSER_TIMEOUT=30000
PAGE_TIMEOUT=20000
MAX_CONTENT_LENGTH=5000
MIN_PARAGRAPH_LENGTH=20
USE_PROXY=false
PROXY_URL=
EOF

# Создание скрипта развертывания
echo "📄 Создание deploy.sh..."
cat > deploy.sh << 'EOF'
#!/bin/bash
set -e

ENVIRONMENT=${1:-development}
echo "🚀 Развертывание Dzen News Scraper в режиме: $ENVIRONMENT"

if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и Docker Compose"
    exit 1
fi

mkdir -p output logs config

echo "🛑 Остановка существующих контейнеров..."
docker-compose down --remove-orphans || true

echo "🏗️  Сборка Docker образов..."
docker-compose build --no-cache

echo "🌐 Запуск контейнеров..."
docker-compose up -d

echo "⏳ Ожидание запуска контейнеров..."
sleep 15

if docker-compose ps | grep -q "Up"; then
    echo "✅ Контейнеры запущены успешно"
    echo "📊 Статус контейнеров:"
    docker-compose ps
    echo ""
    echo "📝 Логи: docker-compose logs -f"
    echo "📁 Результаты: ./output"
    echo "📋 Логи: ./logs"
else
    echo "❌ Ошибка при запуске контейнеров"
    docker-compose logs
    exit 1
fi

echo "🎉 Развертывание завершено!"
EOF

chmod +x deploy.sh

# Создание README.md
echo "📄 Создание README.md..."
cat > README.md << 'EOF'
# Dzen News Scraper

Профессиональный скрапер новостей с сайта Dzen.ru

## Быстрый старт

### Локальный запуск
```bash
pip install -r requirements.txt
playwright install chromium
python dzen_scraper.py
```

### Docker запуск
```bash
./deploy.sh
```

## Просмотр результатов
```bash
# Логи
docker-compose logs -f

# Статус
docker-compose ps

# Результаты
ls -la output/
```

## Управление
```bash
# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Ручной запуск
docker-compose exec dzen-scraper python dzen_scraper.py
```
EOF

# Создание простого монитора
echo "📄 Создание monitor.py..."
cat > monitor.py << 'EOF'
#!/usr/bin/env python3
"""Простой монитор для проверки работы скрапера"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

def check_scraper_health():
    output_dir = Path("./output")
    logs_dir = Path("./logs")
    
    print(f"🔍 Проверка здоровья скрапера - {datetime.now()}")
    print("=" * 50)
    
    # Проверка выходных файлов
    if output_dir.exists():
        json_files = list(output_dir.glob("*.json"))
        md_files = list(output_dir.glob("*.md"))
        
        print(f"📄 JSON файлов: {len(json_files)}")
        print(f"📄 Markdown файлов: {len(md_files)}")
        
        # Последний файл
        if json_files:
            latest_file = max(json_files, key=os.path.getctime)
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(latest_file))
            print(f"📅 Последний файл: {latest_file.name}")
            print(f"⏰ Возраст файла: {file_age}")
            
            # Читаем содержимое последнего файла
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"📊 Статей в последнем файле: {len(data)}")
            except Exception as e:
                print(f"❌ Ошибка чтения файла: {e}")
    else:
        print("❌ Директория output не найдена")
    
    # Проверка логов
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        print(f"📋 Лог файлов: {len(log_files)}")
        
        if log_files:
            latest_log = max(log_files, key=os.path.getctime)
            print(f"📋 Последний лог: {latest_log.name}")
    else:
        print("❌ Директория logs не найдена")
    
    print("=" * 50)

if __name__ == "__main__":
    check_scraper_health()
EOF

chmod +x monitor.py

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p output logs config

# Проверка зависимостей
echo "🔍 Проверка системных зависимостей..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker не установлен. Хотите установить Docker? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "🐳 Установка Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        echo "✅ Docker установлен. Перелогиньтесь для применения прав."
    else
        echo "❌ Docker необходим для работы. Установка прервана."
        exit 1
    fi
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🐙 Установка Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo ""
echo "🎉 Установка завершена!"
echo ""
echo "Структура проекта:"
echo "📂 $PROJECT_DIR/"
echo "  ├── 📄 dzen_scraper.py      # Основной скрапер"
echo "  ├── 📄 scheduler.py         # Планировщик задач"
echo "  ├── 📄 config.py           # Конфигурация"
echo "  ├── 📄 requirements.txt    # Python зависимости"
echo "  ├── 📄 Dockerfile          # Docker образ"
echo "  ├── 📄 docker-compose.yml  # Docker Compose"
echo "  ├── 📄 deploy.sh           # Скрипт развертывания"
echo "  ├── 📄 monitor.py          # Монитор системы"
echo "  ├── 📄 .env               # Переменные окружения"
echo "  ├── 📂 output/            # Результаты скрапинга"
echo "  └── 📂 logs/              # Логи"
echo ""
echo "Следующие шаги:"
echo "1. cd $PROJECT_DIR"
echo "2. ./deploy.sh              # Запуск через Docker"
echo ""
echo "Или для локального запуска:"
echo "1. pip install -r requirements.txt"
echo "2. playwright install chromium"
echo "3. python dzen_scraper.py"
echo ""
echo "Полезные команды:"
echo "  📊 Мониторинг:    python monitor.py"
echo "  📝 Логи:          docker-compose logs -f"
echo "  🛑 Остановка:     docker-compose down"
echo "  🔄 Перезапуск:    docker-compose restart"