#!/usr/bin/env python3
"""
Веб-система администрирования для Dzen News Scraper
Предоставляет интерфейс для управления, мониторинга и настройки скрапера
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel

# Добавляем путь к нашим модулям
sys.path.append('/app')

try:
    from config import Config
    from dzen_scraper import DzenNewsScraper
except ImportError:
    print("Модули скрапера не найдены, создаем заглушки...")
    class Config:
        OUTPUT_DIR = "./output"
        LOGS_DIR = "./logs"
        MAX_ARTICLES = 30

# Инициализация FastAPI
app = FastAPI(
    title="Dzen News Scraper Admin",
    description="Система администрирования для управления новостным скрапером",
    version="1.0.0"
)

# Создание директорий для статики и шаблонов
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
os.makedirs(Config.LOGS_DIR, exist_ok=True)

# Настройка статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic модели для API
class ScraperConfig(BaseModel):
    max_articles: int = 30
    save_format: str = "both"
    min_delay: float = 2.0
    max_delay: float = 4.0
    headless: bool = True
    log_level: str = "INFO"

class ManualRun(BaseModel):
    max_articles: int = 10
    save_format: str = "json"

# Глобальные переменные
scraper_status = {
    "is_running": False,
    "last_run": None,
    "total_runs": 0,
    "total_articles": 0,
    "last_error": None
}

class AdminManager:
    """Менеджер администрирования"""
    
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR)
        self.logs_dir = Path(Config.LOGS_DIR)
        
    async def get_stats(self) -> Dict:
        """Получение статистики работы"""
        stats = {
            "files_count": 0,
            "total_articles": 0,
            "last_file_date": None,
            "log_files_count": 0,
            "disk_usage": 0,
            "uptime": self.get_uptime()
        }
        
        try:
            # Статистика файлов результатов
            if self.output_dir.exists():
                json_files = list(self.output_dir.glob("*.json"))
                stats["files_count"] = len(json_files)
                
                if json_files:
                    # Последний файл
                    latest_file = max(json_files, key=os.path.getctime)
                    stats["last_file_date"] = datetime.fromtimestamp(
                        os.path.getctime(latest_file)
                    ).isoformat()
                    
                    # Подсчет общего количества статей
                    total_articles = 0
                    for file_path in json_files[-10:]:  # Последние 10 файлов
                        try:
                            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                                content = await f.read()
                                data = json.loads(content)
                                total_articles += len(data) if isinstance(data, list) else 1
                        except:
                            continue
                    
                    stats["total_articles"] = total_articles
            
            # Статистика логов
            if self.logs_dir.exists():
                log_files = list(self.logs_dir.glob("*.log"))
                stats["log_files_count"] = len(log_files)
            
            # Использование диска
            if self.output_dir.exists():
                stats["disk_usage"] = sum(
                    f.stat().st_size for f in self.output_dir.rglob('*') if f.is_file()
                ) / (1024 * 1024)  # MB
                
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
        
        return stats
    
    def get_uptime(self) -> str:
        """Получение времени работы системы"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                uptime_delta = timedelta(seconds=uptime_seconds)
                return str(uptime_delta).split('.')[0]  # Убираем микросекунды
        except:
            return "Неизвестно"
    
    async def get_recent_files(self, limit: int = 20) -> List[Dict]:
        """Получение списка последних файлов"""
        files = []
        
        try:
            if self.output_dir.exists():
                json_files = sorted(
                    self.output_dir.glob("*.json"),
                    key=os.path.getctime,
                    reverse=True
                )
                
                for file_path in json_files[:limit]:
                    file_stat = file_path.stat()
                    
                    # Подсчет статей в файле
                    article_count = 0
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                            data = json.loads(content)
                            article_count = len(data) if isinstance(data, list) else 1
                    except:
                        pass
                    
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_stat.st_size,
                        "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                        "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        "articles_count": article_count
                    })
        
        except Exception as e:
            print(f"Ошибка получения файлов: {e}")
        
        return files
    
    async def get_log_content(self, log_file: str, lines: int = 100) -> str:
        """Получение содержимого лог-файла"""
        try:
            log_path = self.logs_dir / log_file
            if not log_path.exists():
                return "Лог-файл не найден"
            
            # Читаем последние N строк
            result = subprocess.run(
                ['tail', '-n', str(lines), str(log_path)],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            return result.stdout if result.returncode == 0 else "Ошибка чтения файла"
        
        except Exception as e:
            return f"Ошибка: {e}"
    
    async def get_rss_feed(self, recent_hours: int = 24) -> str:
        """Генерация RSS фида из последних новостей"""
        try:
            # Находим файлы за последние часы
            cutoff_time = datetime.now() - timedelta(hours=recent_hours)
            recent_files = []
            
            if self.output_dir.exists():
                for file_path in self.output_dir.glob("*.json"):
                    if datetime.fromtimestamp(os.path.getctime(file_path)) > cutoff_time:
                        recent_files.append(file_path)
            
            # Собираем статьи
            all_articles = []
            for file_path in sorted(recent_files, key=os.path.getctime, reverse=True):
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        data = json.loads(content)
                        if isinstance(data, list):
                            all_articles.extend(data)
                except:
                    continue
            
            # Ограничиваем количество статей
            all_articles = all_articles[:50]
            
            # Генерируем RSS
            rss_content = self.generate_rss_xml(all_articles)
            return rss_content
        
        except Exception as e:
            return f"<error>Ошибка генерации RSS: {e}</error>"
    
    def generate_rss_xml(self, articles: List[Dict]) -> str:
        """Генерация RSS XML"""
        from xml.sax.saxutils import escape
        
        rss_items = []
        for article in articles:
            title = escape(article.get('title', 'Без заголовка'))
            url = escape(article.get('url', ''))
            summary = escape(article.get('summary', '')[:200] + '...' if len(article.get('summary', '')) > 200 else article.get('summary', ''))
            pub_date = article.get('scraped_at', datetime.now().isoformat())
            
            # Конвертируем дату в RFC-2822 формат
            try:
                dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                pub_date = dt.strftime('%a, %d %b %Y %H:%M:%S %z')
            except:
                pub_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            rss_items.append(f"""
    <item>
        <title>{title}</title>
        <link>{url}</link>
        <description>{summary}</description>
        <pubDate>{pub_date}</pubDate>
        <guid>{url}</guid>
    </item>""")
        
        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Dzen News Feed</title>
        <description>Автоматически собранные новости с Dzen.ru</description>
        <link>http://dzen.ru/news</link>
        <language>ru-RU</language>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')}</lastBuildDate>
        {''.join(rss_items)}
    </channel>
</rss>"""
        
        return rss_xml

# Создаем экземпляр менеджера
admin = AdminManager()

# API Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Главная страница дашборда"""
    stats = await admin.get_stats()
    recent_files = await admin.get_recent_files(10)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_files": recent_files,
        "scraper_status": scraper_status
    })

@app.get("/api/stats")
async def get_stats():
    """API получения статистики"""
    return await admin.get_stats()

@app.get("/api/files")
async def get_files(limit: int = 20):
    """API получения списка файлов"""
    return await admin.get_recent_files(limit)

@app.get("/api/logs/{log_file}")
async def get_logs(log_file: str, lines: int = 100):
    """API получения логов"""
    content = await admin.get_log_content(log_file, lines)
    return {"content": content}

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Страница просмотра логов"""
    log_files = []
    
    if admin.logs_dir.exists():
        log_files = [
            {
                "name": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in admin.logs_dir.glob("*.log")
        ]
    
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "log_files": log_files
    })

@app.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    """Страница просмотра файлов результатов"""
    files = await admin.get_recent_files(50)
    return templates.TemplateResponse("files.html", {
        "request": request,
        "files": files
    })

@app.get("/api/file/{filename}")
async def get_file_content(filename: str):
    """API получения содержимого файла"""
    try:
        file_path = admin.output_dir / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Если это JSON, парсим и возвращаем структурированно
        if filename.endswith('.json'):
            try:
                data = json.loads(content)
                return {"type": "json", "content": data}
            except:
                pass
        
        return {"type": "text", "content": content}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rss.xml")
async def rss_feed(hours: int = 24):
    """RSS фид последних новостей"""
    rss_content = await admin.get_rss_feed(hours)
    return HTMLResponse(content=rss_content, media_type="application/rss+xml")

@app.post("/api/run-scraper")
async def run_scraper_manually(config: ManualRun, background_tasks: BackgroundTasks):
    """API ручного запуска скрапера"""
    if scraper_status["is_running"]:
        raise HTTPException(status_code=409, detail="Скрапер уже запущен")
    
    background_tasks.add_task(run_scraper_background, config)
    return {"status": "started", "message": "Скрапер запущен в фоне"}

async def run_scraper_background(config: ManualRun):
    """Фоновое выполнение скрапера"""
    global scraper_status
    
    scraper_status["is_running"] = True
    scraper_status["last_run"] = datetime.now().isoformat()
    
    try:
        # Создаем экземпляр скрапера
        scraper = DzenNewsScraper()
        await scraper.run_scraper(
            max_articles=config.max_articles,
            save_format=config.save_format
        )
        
        scraper_status["total_runs"] += 1
        scraper_status["total_articles"] += len(scraper.collected_articles)
        scraper_status["last_error"] = None
        
    except Exception as e:
        scraper_status["last_error"] = str(e)
        print(f"Ошибка выполнения скрапера: {e}")
    
    finally:
        scraper_status["is_running"] = False

@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Страница конфигурации"""
    current_config = {
        "max_articles": getattr(Config, 'MAX_ARTICLES', 30),
        "save_format": getattr(Config, 'SAVE_FORMAT', 'both'),
        "min_delay": getattr(Config, 'MIN_DELAY', 2.0),
        "max_delay": getattr(Config, 'MAX_DELAY', 4.0),
        "headless": getattr(Config, 'HEADLESS', True),
        "log_level": getattr(Config, 'LOG_LEVEL', 'INFO')
    }
    
    return templates.TemplateResponse("config.html", {
        "request": request,
        "config": current_config
    })

@app.post("/api/update-config")
async def update_config(config: ScraperConfig):
    """API обновления конфигурации"""
    try:
        # Обновляем .env файл
        env_lines = []
        env_path = Path(".env")
        
        if env_path.exists():
            async with aiofiles.open(env_path, 'r') as f:
                env_lines = (await f.read()).split('\n')
        
        # Обновляем или добавляем настройки
        config_map = {
            'MAX_ARTICLES': str(config.max_articles),
            'SAVE_FORMAT': config.save_format,
            'MIN_DELAY': str(config.min_delay),
            'MAX_DELAY': str(config.max_delay),
            'HEADLESS': str(config.headless).lower(),
            'LOG_LEVEL': config.log_level
        }
        
        # Обновляем существующие или добавляем новые
        updated_lines = []
        updated_keys = set()
        
        for line in env_lines:
            if '=' in line and not line.startswith('#'):
                key = line.split('=')[0]
                if key in config_map:
                    updated_lines.append(f"{key}={config_map[key]}")
                    updated_keys.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Добавляем новые ключи
        for key, value in config_map.items():
            if key not in updated_keys:
                updated_lines.append(f"{key}={value}")
        
        # Сохраняем
        async with aiofiles.open(env_path, 'w') as f:
            await f.write('\n'.join(updated_lines))
        
        return {"status": "success", "message": "Конфигурация обновлена"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления: {e}")

@app.get("/api/docker-status")
async def get_docker_status():
    """Получение статуса Docker контейнеров"""
    try:
        result = subprocess.run(
            ['docker-compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        
        if result.returncode == 0:
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        containers.append(json.loads(line))
                    except:
                        pass
            return {"containers": containers}
        else:
            return {"error": "Не удалось получить статус контейнеров"}
    
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Создание шаблонов при первом запуске
    create_templates()
    create_static_files()
    
    # Запуск сервера
    uvicorn.run(
        "admin_app:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )


def create_templates():
    """Создание HTML шаблонов"""
    # Шаблоны будут созданы в следующем артефакте
    pass

def create_static_files():
    """Создание статических файлов CSS/JS"""
    # Статические файлы будут созданы в следующем артефакте  
    pass