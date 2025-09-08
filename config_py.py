"""
Конфигурация для Dzen News Scraper
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Основные настройки
    BASE_URL = "https://dzen.ru/news"
    MAX_ARTICLES = int(os.getenv('MAX_ARTICLES', '30'))
    SAVE_FORMAT = os.getenv('SAVE_FORMAT', 'json')  # json, markdown, both
    
    # Настройки браузера
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', '30000'))
    PAGE_TIMEOUT = int(os.getenv('PAGE_TIMEOUT', '20000'))
    
    # Настройки задержек
    MIN_DELAY = float(os.getenv('MIN_DELAY', '1.0'))
    MAX_DELAY = float(os.getenv('MAX_DELAY', '3.0'))
    ARTICLE_DELAY_MIN = float(os.getenv('ARTICLE_DELAY_MIN', '2.0'))
    ARTICLE_DELAY_MAX = float(os.getenv('ARTICLE_DELAY_MAX', '5.0'))
    
    # Директории
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')
    LOGS_DIR = os.getenv('LOGS_DIR', './logs')
    
    # Настройки контента
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '5000'))
    MIN_PARAGRAPH_LENGTH = int(os.getenv('MIN_PARAGRAPH_LENGTH', '20'))
    
    # Прокси настройки (если необходимо)
    USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
    PROXY_URL = os.getenv('PROXY_URL', '')
    
    # User Agents для ротации
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
    
    # Селекторы для парсинга
    SELECTORS = {
        'news_cards': 'article[data-testid="news-card"], .news-card, [data-entity="news-card"], .mg-card',
        'card_title': 'h2, .news-card__title, [data-testid="news-card-title"], .mg-card__title',
        'card_link': 'a',
        'card_summary': '.news-card__lead, .news-card__text, .mg-card__text, p',
        'article_content': 'article, .article-content, .news-content, [data-testid="article-content"], .mg-story-text',
        'article_text': 'p, .paragraph, .mg-story-text p',
        'publish_date': 'time, .publish-date, [data-testid="publish-date"], .mg-story-date'
    }
    
    # Настройки логирования
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def create_directories(cls):
        """Создание необходимых директорий"""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.LOGS_DIR, exist_ok=True)