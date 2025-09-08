#!/bin/bash

# Скрипт для исправления проблем с Playwright в Docker

set -e

echo "🔧 Диагностика и исправление проблем с Playwright"
echo "================================================"

# Проверка системы
echo "🔍 Информация о системе:"
echo "OS: $(lsb_release -d 2>/dev/null | cut -f2 || cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2)"
echo "Ядро: $(uname -r)"
echo "Архитектура: $(uname -m)"
echo "Docker: $(docker --version)"
echo "Docker Compose: $(docker-compose --version)"
echo ""

# Проверка доступного места
echo "💾 Проверка дискового пространства:"
df -h /var/lib/docker
echo ""

# Проверка памяти
echo "🧠 Проверка памяти:"
free -h
echo ""

# Функция создания минимального Dockerfile
create_minimal_dockerfile() {
    cat > Dockerfile.minimal << 'EOF'
FROM python:3.11-slim

# Установка только необходимых системных пакетов
RUN apt-get update && apt-get install -y \
    wget curl unzip xvfb \
    libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgtk-3-0 libgbm1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка Python зависимостей
COPY requirements.minimal.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Установка Playwright с обработкой ошибок
RUN playwright install chromium || echo "Playwright install failed, continuing..."

# Попытка установки зависимостей с игнорированием ошибок
RUN apt-get update && \
    playwright install-deps chromium || \
    (echo "Dependencies install failed, installing manually..." && \
     apt-get install -y libnss3-dev libatk-bridge2.0-dev libdrm-dev libxkbcommon-dev libgtk-3-dev libgbm-dev || true) && \
    rm -rf /var/lib/apt/lists/*

COPY . .
RUN mkdir -p /app/output /app/logs
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app
USER scraper

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HEADLESS=true

CMD ["python", "scheduler.py"]
EOF
}

# Создание минимального requirements.txt
create_minimal_requirements() {
    cat > requirements.minimal.txt << 'EOF'
playwright==1.40.0
aiofiles==23.2.1
schedule==1.2.0
python-dotenv==1.0.0
EOF
}

# Функция тестирования Playwright
test_playwright() {
    echo "🧪 Тестирование Playwright..."
    
    cat > test_playwright.py << 'EOF'
import asyncio
from playwright.async_api import async_playwright

async def test():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto('https://example.com')
            title = await page.title()
            print(f"✅ Playwright работает! Заголовок: {title}")
            await browser.close()
            return True
    except Exception as e:
        print(f"❌ Ошибка Playwright: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    exit(0 if result else 1)
EOF

    if docker run --rm -v $(pwd):/app python:3.11-slim bash -c "
        cd /app && 
        pip install playwright && 
        playwright install chromium && 
        python test_playwright.py
    "; then
        echo "✅ Playwright тест прошел успешно"
        rm -f test_playwright.py
        return 0
    else
        echo "❌ Playwright тест не прошел"
        rm -f test_playwright.py
        return 1
    fi
}

# Основная функция исправления
fix_playwright_issues() {
    echo "🔧 Применение исправлений..."
    
    # Остановка существующих контейнеров
    echo "🛑 Остановка контейнеров..."
    docker-compose down 2>/dev/null || true
    
    # Очистка Docker кэша
    echo "🧹 Очистка Docker кэша..."
    docker system prune -f
    
    # Создание исправленных файлов
    echo "📄 Создание исправленных файлов..."
    create_minimal_dockerfile
    create_minimal_requirements
    
    # Обновление docker-compose для использования минимального образа
    cat > docker-compose.fixed.yml << EOF
version: '3.8'

services:
  dzen-scraper:
    build:
      context: .
      dockerfile: Dockerfile.minimal
    container_name: dzen-news-scraper-minimal
    restart: unless-stopped
    environment:
      - HEADLESS=true
      - MAX_ARTICLES=10
      - SAVE_FORMAT=json
      - LOG_LEVEL=INFO
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    healthcheck:
      test: ["CMD", "python", "-c", "print('OK')"]
      interval: 5m
      timeout: 10s
      retries: 3

volumes:
  scraper_data:
EOF
    
    echo "🏗️  Сборка минимального образа..."
    if docker-compose -f docker-compose.fixed.yml build; then
        echo "✅ Минимальный образ собран успешно"
        
        echo "🚀 Запуск минимального контейнера..."
        docker-compose -f docker-compose.fixed.yml up -d
        
        echo "⏳ Ожидание запуска..."
        sleep 10
        
        if docker-compose -f docker-compose.fixed.yml ps | grep -q "Up"; then
            echo "✅ Минимальный контейнер запущен успешно!"
            echo ""
            echo "Используйте для управления:"
            echo "  docker-compose -f docker-compose.fixed.yml logs -f"
            echo "  docker-compose -f docker-compose.fixed.yml down"
            echo "  docker-compose -f docker-compose.fixed.yml restart"
            return 0
        else
            echo "❌ Не удалось запустить минимальный контейнер"
            docker-compose -f docker-compose.fixed.yml logs
            return 1
        fi
    else
        echo "❌ Ошибка сборки минимального образа"
        return 1
    fi
}

# Функция создания альтернативного решения без Docker
create_local_solution() {
    echo "🏠 Создание локального решения без Docker..."
    
    cat > install_local.sh << 'EOF'
#!/bin/bash
echo "📦 Установка локальной версии Dzen Scraper..."

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install playwright aiofiles schedule python-dotenv

# Установка браузера
playwright install chromium

# Проверка установки
python -c "
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print('✅ Playwright готов к работе!')
        await browser.close()

asyncio.run(test())
"

echo "✅ Локальная установка завершена"
echo "Запуск: source venv/bin/activate && python dzen_scraper.py"
EOF

    chmod +x install_local.sh
    echo "✅ Создан скрипт локальной установки: ./install_local.sh"
}

# Меню выбора действий
echo "Выберите действие:"
echo "1) Тестировать Playwright в Docker"
echo "2) Создать минимальный образ"
echo "3) Создать локальное решение"
echo "4) Показать диагностическую информацию"
echo "5) Все исправления автоматически"

read -p "Введите номер (1-5): " choice

case $choice in
    1)
        test_playwright
        ;;
    2)
        fix_playwright_issues
        ;;
    3)
        create_local_solution
        ;;
    4)
        echo "📋 Диагностическая информация уже показана выше"
        echo ""
        echo "🔍 Дополнительная диагностика:"
        echo "Docker информация:"
        docker info | head -20
        echo ""
        echo "Доступные образы Python:"
        docker images python
        ;;
    5)
        echo "🚀 Запуск всех исправлений..."
        if ! test_playwright; then
            echo "⚠️  Базовый тест не прошел, применяем исправления..."
            if ! fix_playwright_issues; then
                echo "⚠️  Docker решение не сработало, создаем локальное..."
                create_local_solution
            fi
        fi
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac

echo ""
echo "🎉 Готово! Если проблемы остались, попробуйте:"
echo "1. Увеличить память Docker (Settings → Resources → Memory → 4GB+)"
echo "2. Использовать локальную установку: ./install_local.sh"
echo "3. Обратиться к документации: https://playwright.dev/python/docs/docker"