#!/bin/bash

# Скрипт настройки сервера для Dzen News Scraper
# Для Ubuntu/Debian серверов

set -e

echo "🔧 Настройка сервера для Dzen News Scraper"

# Обновление системы
echo "📦 Обновление системы..."
sudo apt-get update
sudo apt-get upgrade -y

# Установка необходимых пакетов
echo "📦 Установка базовых пакетов..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    nano \
    cron \
    logrotate

# Установка Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo "✅ Docker уже установлен"
fi

# Установка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🐙 Установка Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "✅ Docker Compose уже установлен"
fi

# Создание пользователя для скрапера
if ! id "scraper" &>/dev/null; then
    echo "👤 Создание пользователя scraper..."
    sudo useradd -m -s /bin/bash scraper
    sudo usermod -aG docker scraper
else
    echo "✅ Пользователь scraper уже существует"
fi

# Создание рабочей директории
echo "📁 Создание рабочей директории..."
sudo mkdir -p /opt/dzen-scraper
sudo chown scraper:scraper /opt/dzen-scraper

# Настройка ротации логов
echo "📋 Настройка ротации логов..."
sudo tee /etc/logrotate.d/dzen-scraper > /dev/null << EOF
/opt/dzen-scraper/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF

# Создание systemd сервиса
echo "🔧 Создание systemd сервиса..."
sudo tee /etc/systemd/system/dzen-scraper.service > /dev/null << EOF
[Unit]
Description=Dzen News Scraper
Requires=docker.service
After=docker.service

[Service]
Type=forking
Restart=always
RestartSec=10
User=scraper
Group=scraper
WorkingDirectory=/opt/dzen-scraper
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable dzen-scraper

# Настройка брандмауэра
echo "🔥 Настройка брандмауэра..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8080  # Для веб-интерфейса (если используется)

# Создание скрипта мониторинга
echo "📊 Создание скрипта мониторинга..."
sudo tee /opt/dzen-scraper/monitor.sh > /dev/null << 'EOF'
#!/bin/bash

# Скрипт мониторинга Dzen Scraper
LOG_FILE="/opt/dzen-scraper/logs/monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Проверка работы контейнера
if docker-compose ps | grep -q "Up"; then
    echo "[$DATE] ✅ Контейнер работает" >> $LOG_FILE
else
    echo "[$DATE] ❌ Контейнер не работает, перезапуск..." >> $LOG_FILE
    docker-compose restart
fi

# Проверка размера логов
LOG_SIZE=$(du -sm /opt/dzen-scraper/logs/ | cut -f1)
if [ $LOG_SIZE -gt 1000 ]; then
    echo "[$DATE] ⚠️  Логи занимают ${LOG_SIZE}MB, требуется очистка" >> $LOG_FILE
fi

# Проверка свободного места
DISK_USAGE=$(df /opt/dzen-scraper | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "[$DATE] ⚠️  Диск заполнен на ${DISK_USAGE}%" >> $LOG_FILE
fi
EOF

chmod +x /opt/dzen-scraper/monitor.sh

# Добавление задач в cron
echo "⏰ Настройка cron задач..."
sudo tee /tmp/scraper-cron > /dev/null << EOF
# Мониторинг каждые 30 минут
*/30 * * * * /opt/dzen-scraper/monitor.sh

# Перезапуск контейнера раз в день в 3:00
0 3 * * * cd /opt/dzen-scraper && docker-compose restart

# Очистка старых файлов результатов (старше 7 дней)
0 2 * * * find /opt/dzen-scraper/output -name "*.json" -mtime +7 -delete
0 2 * * * find /opt/dzen-scraper/output -name "*.md" -mtime +7 -delete
EOF

sudo crontab -u scraper /tmp/scraper-cron
rm /tmp/scraper-cron

# Создание скрипта обновления
echo "🔄 Создание скрипта обновления..."
sudo tee /opt/dzen-scraper/update.sh > /dev/null << 'EOF'
#!/bin/bash

# Скрипт обновления Dzen Scraper
cd /opt/dzen-scraper

echo "🔄 Обновление Dzen News Scraper..."

# Остановка контейнеров
docker-compose down

# Получение обновлений
git pull origin main

# Пересборка образов
docker-compose build --no-cache

# Запуск
docker-compose up -d

echo "✅ Обновление завершено"
EOF

chmod +x /opt/dzen-scraper/update.sh

echo ""
echo "🎉 Настройка сервера завершена!"
echo ""
echo "Следующие шаги:"
echo "1. Перелогиньтесь для применения прав Docker: sudo su - scraper"
echo "2. Перейдите в рабочую директорию: cd /opt/dzen-scraper"
echo "3. Склонируйте репозиторий с кодом или скопируйте файлы проекта"
echo "4. Запустите развертывание: ./deploy.sh production"
echo ""
echo "Полезные команды:"
echo "  Статус сервиса:     sudo systemctl status dzen-scraper"
echo "  Запуск сервиса:     sudo systemctl start dzen-scraper"
echo "  Остановка сервиса:  sudo systemctl stop dzen-scraper"
echo "  Обновление:         /opt/dzen-scraper/update.sh"
echo "  Мониторинг:         /opt/dzen-scraper/monitor.sh"