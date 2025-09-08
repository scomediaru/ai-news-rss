# Полное руководство по развертыванию Dzen News Scraper

## 🚀 Быстрое развертывание (рекомендуемый способ)

### Вариант 1: Автоматическая установка одной командой

```bash
curl -fsSL https://raw.githubusercontent.com/your-username/dzen-news-scraper/main/quick_install.sh | bash
cd dzen-news-scraper
./deploy.sh
```

### Вариант 2: Пошаговая установка

1. **Создание проекта**
```bash
mkdir dzen-news-scraper && cd dzen-news-scraper
```

2. **Скачивание файлов** (скопируйте все файлы из артефактов выше)

3. **Запуск**
```bash
chmod +x deploy.sh
./deploy.sh
```

## 🖥️ Развертывание на сервере

### Подготовка сервера (Ubuntu/Debian)

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y curl wget git htop

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перелогинивание для применения прав Docker
exit
# Войти обратно по SSH
```

### Настройка проекта на сервере

```bash
# Создание рабочей директории
mkdir -p /opt/dzen-scraper
cd /opt/dzen-scraper

# Копирование файлов проекта (через git, scp или другим способом)
# Например, через git:
git clone https://github.com/your-username/dzen-news-scraper.git .

# Или скачивание архива:
wget https://github.com/your-username/dzen-news-scraper/archive/main.zip
unzip main.zip && mv dzen-news-scraper-main/* . && rm -rf dzen-news-scraper-main main.zip

# Настройка прав
chmod +x deploy.sh monitor.py
```

### Конфигурация для production

```bash
# Редактирование .env для production
nano .env
```

Рекомендуемые настройки для production:
```env
MAX_ARTICLES=50
SAVE_FORMAT=both
HEADLESS=true
LOG_LEVEL=INFO
MIN_DELAY=3.0
MAX_DELAY=6.0
ARTICLE_DELAY_MIN=5.0
ARTICLE_DELAY_MAX=10.0
```

### Запуск в production

```bash
# Развертывание
./deploy.sh production

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

## ⚙️ Настройка systemd сервиса

Для автоматического запуска при загрузке системы:

```bash
# Создание systemd сервиса
sudo tee /etc/systemd/system/dzen-scraper.service << EOF
[Unit]
Description=Dzen News Scraper
Requires=docker.service
After=docker.service

[Service]
Type=forking
Restart=always
RestartSec=10
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd и включение сервиса
sudo systemctl daemon-reload
sudo systemctl enable dzen-scraper
sudo systemctl start dzen-scraper

# Проверка статуса сервиса
sudo systemctl status dzen-scraper
```

## 📋 Настройка логирования

### Ротация логов

```bash
# Создание конфигурации logrotate
sudo tee /etc/logrotate.d/dzen-scraper << EOF
$(pwd)/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su $USER $USER
}
EOF

# Тестирование ротации
sudo logrotate -d /etc/logrotate.d/dzen-scraper
```

### Мониторинг логов

```bash
# Просмотр логов в реальном времени
docker-compose logs -f --tail=100

# Логи только скрапера
docker-compose logs -f dzen-scraper

# Поиск ошибок в логах
docker-compose logs | grep -i error

# Архивные логи
ls -la logs/
```

## ⏰ Настройка cron задач

```bash
# Открытие crontab
crontab -e

# Добавление задач мониторинга
# Проверка здоровья каждые 30 минут
*/30 * * * * cd /opt/dzen-scraper && python3 monitor.py >> logs/monitor.log 2>&1

# Перезапуск контейнера раз в день в 3:00
0 3 * * * cd /opt/dzen-scraper && docker-compose restart

# Очистка старых файлов результатов (старше 7 дней)
0 2 * * * find /opt/dzen-scraper/output -name "*.json" -mtime +7 -delete
0 2 * * * find /opt/dzen-scraper/output -name "*.md" -mtime +7 -delete

# Еженедельная очистка логов Docker
0 4 * * 0 docker system prune -f
```

## 🔧 Конфигурация Nginx (опционально)

Если нужен веб-доступ к результатам:

```bash
# Установка Nginx
sudo apt install -y nginx

# Создание конфигурации
sudo tee /etc/nginx/sites-available/dzen-scraper << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    location /results/ {
        alias /opt/dzen-scraper/output/;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
    }
    
    location /logs/ {
        alias /opt/dzen-scraper/logs/;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
        auth_basic "Restricted Content";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
EOF

# Включение сайта
sudo ln -s /etc/nginx/sites-available/dzen-scraper /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

## 🛡️ Безопасность

### Настройка брандмауэра

```bash
# Включение UFW
sudo ufw --force enable

# Базовые правила
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешение SSH
sudo ufw allow ssh

# Разрешение HTTP/HTTPS (если используется Nginx)
sudo ufw allow 'Nginx Full'

# Проверка статуса
sudo ufw status
```

### Ограничение ресурсов Docker

В `docker-compose.yml` уже настроены ограичения:

```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 512M
      cpus: '0.5'
```

## 📊 Мониторинг и алерты

### Простой скрипт мониторинга

```bash
# Создание скрипта проверки здоровья
cat > health_check.sh << 'EOF'
#!/bin/bash

WEBHOOK_URL="YOUR_SLACK_WEBHOOK_URL"  # Замените на ваш webhook

check_container() {
    if ! docker-compose ps | grep -q "Up"; then
        curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"🚨 Dzen Scraper контейнер не работает!"}' \
            $WEBHOOK_URL
        docker-compose restart
    fi
}

check_disk_space() {
    DISK_USAGE=$(df /opt/dzen-scraper | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt 90 ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"⚠️ Диск заполнен на ${DISK_USAGE}%\"}" \
            $WEBHOOK_URL
    fi
}

check_recent_files() {
    LAST_FILE=$(find output -name "*.json" -mtime -1 | wc -l)
    if [ $LAST_FILE -eq 0 ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"📄 Нет новых файлов за последние 24 часа"}' \
            $WEBHOOK_URL
    fi
}

check_container
check_disk_space
check_recent_files
EOF

chmod +x health_check.sh

# Добавление в cron (каждый час)
echo "0 * * * * cd /opt/dzen-scraper && ./health_check.sh" | crontab -
```

## 🔄 Обновление

### Скрипт обновления

```bash
cat > update.sh << 'EOF'
#!/bin/bash

echo "🔄 Обновление Dzen News Scraper..."

# Остановка контейнеров
docker-compose down

# Создание бэкапа
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz output/ logs/ .env

# Получение обновлений (если используется git)
git pull origin main

# Пересборка образов
docker-compose build --no-cache

# Запуск
docker-compose up -d

echo "✅ Обновление завершено"
EOF

chmod +x update.sh
```

## 🚨 Решение проблем с Playwright

### Проблема с зависимостями (ttf-ubuntu-font-family, ttf-unifont)

Эта ошибка возникает в новых версиях Debian/Ubuntu. Вот несколько решений:

#### Решение 1: Автоматическое исправление

```bash
# Скачайте и запустите скрипт исправления
wget https://your-server.com/fix_playwright.sh
chmod +x fix_playwright.sh
./fix_playwright.sh
```

Выберите опцию "5" для автоматического применения всех исправлений.

#### Решение 2: Использование Ubuntu образа

```bash
# Замените в docker-compose.yml:
services:
  dzen-scraper:
    build:
      context: .
      dockerfile: Dockerfile.ubuntu  # Вместо Dockerfile
```

#### Решение 3: Локальная установка без Docker

```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install playwright aiofiles schedule python-dotenv

# Установка браузера Playwright
playwright install chromium

# Запуск скрапера
python dzen_scraper.py
```

#### Решение 4: Исправленный деплой

```bash
# Используйте исправленный скрипт развертывания
./deploy_fixed.sh
```

Этот скрипт автоматически определит подходящий Docker образ для вашей системы.

### Дополнительные команды для диагностики

```bash
# Проверка системы
lsb_release -a
docker --version
free -h
df -h

# Очистка Docker
docker system prune -a -f
docker volume prune -f

# Ручная сборка с отладкой
docker build -t test-playwright -f Dockerfile.ubuntu . --progress=plain --no-cache
```

### Частые проблемы

1. **Контейнер не запускается**
```bash
# Проверка логов
docker-compose logs

# Проверка ресурсов
docker system df
docker stats

# Пересборка без кэша
docker-compose build --no-cache
```

2. **Проблемы с памятью**
```bash
# Очистка Docker
docker system prune -a

# Проверка потребления памяти
free -h
docker stats
```

3. **Не собираются новости**
```bash
# Запуск в debug режиме
HEADLESS=false LOG_LEVEL=DEBUG python3 dzen_scraper.py

# Проверка селекторов
docker-compose exec dzen-scraper python3 -c "from config import Config; print(Config.SELECTORS)"
```

4. **Проблемы с правами**
```bash
# Исправление прав
sudo chown -R $USER:$USER /opt/dzen-scraper
chmod +x deploy.sh monitor.py update.sh
```

### Логи для диагностики

```bash
# Системные логи
sudo journalctl -u dzen-scraper.service -f

# Docker логи
docker-compose logs --tail=1000

# Логи планировщика
tail -f logs/scheduler.log

# Логи скрапера
tail -f logs/dzen_scraper.log
```

## 📈 Оптимизация производительности

### Настройки для высокой нагрузки

```env
# В .env файле
MAX_ARTICLES=100
MIN_DELAY=1.0
MAX_DELAY=2.0
ARTICLE_DELAY_MIN=2.0
ARTICLE_DELAY_MAX=4.0
```

### Использование прокси

```env
# В .env файле
USE_PROXY=true
PROXY_URL=http://proxy:port
```

### Масштабирование

```yaml
# В docker-compose.yml для нескольких экземпляров
version: '3.8'

services:
  dzen-scraper-1:
    build: .
    container_name: dzen-news-scraper-1
    environment:
      - MAX_ARTICLES=25

  dzen-scraper-2:
    build: .
    container_name: dzen-news-scraper-2
    environment:
      - MAX_ARTICLES=25
```

## ✅ Чеклист развертывания

- [ ] Установлен Docker и Docker Compose
- [ ] Созданы все файлы проекта
- [ ] Настроен .env файл
- [ ] Запущены контейнеры
- [ ] Проверена работа скрапера
- [ ] Настроена ротация логов
- [ ] Добавлены cron задачи
- [ ] Настроен systemd сервис
- [ ] Проверен мониторинг
- [ ] Настроена безопасность (firewall)
- [ ] Создан скрипт обновления
- [ ] Протестировано восстановление после сбоев

Развертывание завершено! 🎉