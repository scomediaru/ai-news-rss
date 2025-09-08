#!/usr/bin/env python3
"""
Dzen.ru News Scraper
Собирает заголовки, ссылки, саммари и полные тексты новостей с dzen.ru/news
Использует Playwright для обхода защиты от ботов
"""

import asyncio
import json
import logging
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, Page
import aiofiles


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dzen_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DzenNewsScraper:
    def __init__(self):
        self.base_url = "https://dzen.ru/news"
        self.browser: Optional[Browser] = None
        self.collected_articles: List[Dict] = []
        
        # User agents для ротации
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # Селекторы для парсинга
        self.selectors = {
            'news_cards': 'article[data-testid="news-card"], .news-card, [data-entity="news-card"]',
            'card_title': 'h2, .news-card__title, [data-testid="news-card-title"]',
            'card_link': 'a',
            'card_summary': '.news-card__lead, .news-card__text, p',
            'article_content': 'article, .article-content, .news-content, [data-testid="article-content"]',
            'article_text': 'p, .paragraph',
            'publish_date': 'time, .publish-date, [data-testid="publish-date"]'
        }

    async def init_browser(self) -> Browser:
        """Инициализация браузера с настройками для обхода защиты"""
        playwright = await async_playwright().start()
        
        # Настройки браузера для обхода детекции ботов
        browser = await playwright.chromium.launch(
            headless=True,  # Можно поставить False для отладки
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        self.browser = browser
        return browser

    async def create_stealth_page(self) -> Page:
        """Создание страницы с эмуляцией человеческого поведения"""
        context = await self.browser.new_context(
            user_agent=random.choice(self.user_agents),
            viewport={'width': 1920, 'height': 1080},
            locale='ru-RU',
            timezone_id='Europe/Moscow'
        )
        
        page = await context.new_page()
        
        # Удаляем признаки автоматизации
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            window.chrome = {
                runtime: {},
            };
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ru-RU', 'ru', 'en-US', 'en'],
            });
        """)
        
        return page

    async def human_like_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Имитация человеческих задержек"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    async def get_news_cards(self, page: Page) -> List[Dict]:
        """Получение карточек новостей с главной страницы"""
        logger.info("Загрузка главной страницы Dzen...")
        
        try:
            # Переходим на страницу новостей
            await page.goto(self.base_url, wait_until='networkidle', timeout=30000)
            await self.human_like_delay(2, 4)
            
            # Ждем загрузки контента
            await page.wait_for_selector(self.selectors['news_cards'], timeout=15000)
            await self.human_like_delay(1, 2)
            
            # Прокручиваем страницу для загрузки дополнительного контента
            await self.scroll_page(page)
            
            # Получаем все карточки новостей
            cards = await page.query_selector_all(self.selectors['news_cards'])
            logger.info(f"Найдено {len(cards)} карточек новостей")
            
            news_items = []
            
            for i, card in enumerate(cards[:50]):  # Ограничиваем количество для демонстрации
                try:
                    title_elem = await card.query_selector(self.selectors['card_title'])
                    link_elem = await card.query_selector(self.selectors['card_link'])
                    summary_elem = await card.query_selector(self.selectors['card_summary'])
                    
                    if title_elem and link_elem:
                        title = await title_elem.inner_text()
                        href = await link_elem.get_attribute('href')
                        summary = await summary_elem.inner_text() if summary_elem else ""
                        
                        # Формируем полную ссылку
                        full_url = urljoin(self.base_url, href) if href else ""
                        
                        if title and full_url and self.is_valid_news_url(full_url):
                            news_items.append({
                                'title': title.strip(),
                                'url': full_url,
                                'summary': summary.strip()[:300] if summary else "",
                                'scraped_at': datetime.now().isoformat()
                            })
                            logger.debug(f"Обработана карточка {i+1}: {title[:50]}...")
                        
                except Exception as e:
                    logger.warning(f"Ошибка при обработке карточки {i+1}: {e}")
                    continue
            
            logger.info(f"Успешно собрано {len(news_items)} новостных карточек")
            return news_items
            
        except Exception as e:
            logger.error(f"Ошибка при получении карточек новостей: {e}")
            return []

    async def scroll_page(self, page: Page):
        """Прокрутка страницы для загрузки дополнительного контента"""
        try:
            # Постепенная прокрутка
            for i in range(3):
                await page.evaluate(f"window.scrollTo(0, {(i + 1) * 1000})")
                await self.human_like_delay(1, 2)
                
            # Прокрутка вверх
            await page.evaluate("window.scrollTo(0, 0)")
            await self.human_like_delay(1, 2)
            
        except Exception as e:
            logger.warning(f"Ошибка при прокрутке: {e}")

    def is_valid_news_url(self, url: str) -> bool:
        """Проверка валидности URL новости"""
        if not url:
            return False
            
        parsed = urlparse(url)
        if not parsed.netlify or 'dzen.ru' not in parsed.netlify:
            return False
            
        # Исключаем нежелательные URL
        exclude_patterns = ['/video/', '/profile/', '/media/', '/live/']
        return not any(pattern in url for pattern in exclude_patterns)

    async def get_article_content(self, page: Page, url: str) -> Dict:
        """Получение полного содержимого статьи"""
        logger.debug(f"Получение контента статьи: {url}")
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=20000)
            await self.human_like_delay(1, 3)
            
            # Ищем контент статьи
            content_elem = await page.query_selector(self.selectors['article_content'])
            if not content_elem:
                # Альтернативные селекторы
                content_elem = await page.query_selector('main, .content, .post-content')
            
            content = ""
            publish_date = ""
            
            if content_elem:
                # Получаем текстовые параграфы
                paragraphs = await content_elem.query_selector_all(self.selectors['article_text'])
                content_parts = []
                
                for p in paragraphs:
                    text = await p.inner_text()
                    if text and len(text.strip()) > 20:  # Фильтруем короткие строки
                        content_parts.append(text.strip())
                
                content = '\n\n'.join(content_parts)
            
            # Ищем дату публикации
            date_elem = await page.query_selector(self.selectors['publish_date'])
            if date_elem:
                publish_date = await date_elem.get_attribute('datetime')
                if not publish_date:
                    publish_date = await date_elem.inner_text()
            
            return {
                'content': content[:5000] if content else "",  # Ограничиваем размер
                'publish_date': publish_date,
                'content_length': len(content)
            }
            
        except Exception as e:
            logger.warning(f"Ошибка при получении контента {url}: {e}")
            return {'content': "", 'publish_date': "", 'content_length': 0}

    async def scrape_full_articles(self, news_items: List[Dict]) -> List[Dict]:
        """Получение полного содержимого для всех статей"""
        logger.info(f"Начинаем сбор полного контента для {len(news_items)} статей...")
        
        page = await self.create_stealth_page()
        enriched_articles = []
        
        for i, item in enumerate(news_items):
            try:
                logger.info(f"Обрабатываем статью {i+1}/{len(news_items)}: {item['title'][:50]}...")
                
                # Получаем полный контент
                article_data = await self.get_article_content(page, item['url'])
                
                # Объединяем данные
                full_article = {**item, **article_data}
                enriched_articles.append(full_article)
                
                # Задержка между запросами
                await self.human_like_delay(2, 5)
                
            except Exception as e:
                logger.error(f"Ошибка при обработке статьи {item['url']}: {e}")
                enriched_articles.append(item)  # Добавляем без контента
                continue
        
        await page.close()
        logger.info(f"Завершен сбор контента. Обработано {len(enriched_articles)} статей")
        return enriched_articles

    async def save_results(self, articles: List[Dict], format_type: str = 'json'):
        """Сохранение результатов в различных форматах"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type == 'json':
            filename = f'dzen_news_{timestamp}.json'
            async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(articles, ensure_ascii=False, indent=2))
            logger.info(f"Результаты сохранены в {filename}")
            
        elif format_type == 'markdown':
            filename = f'dzen_news_{timestamp}.md'
            content = self.generate_markdown_report(articles)
            async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
                await f.write(content)
            logger.info(f"Markdown отчет сохранен в {filename}")

    def generate_markdown_report(self, articles: List[Dict]) -> str:
        """Генерация Markdown отчета"""
        report = f"# Новости Dzen.ru\n\n"
        report += f"**Дата сбора:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Количество статей:** {len(articles)}\n\n"
        
        for i, article in enumerate(articles, 1):
            report += f"## {i}. {article['title']}\n\n"
            report += f"**URL:** {article['url']}\n\n"
            
            if article.get('publish_date'):
                report += f"**Дата публикации:** {article['publish_date']}\n\n"
            
            if article.get('summary'):
                report += f"**Краткое описание:** {article['summary']}\n\n"
            
            if article.get('content'):
                report += f"**Полный текст:**\n{article['content'][:1000]}...\n\n"
            
            report += "---\n\n"
        
        return report

    async def run_scraper(self, max_articles: int = 30, save_format: str = 'json'):
        """Основной метод запуска скрапера"""
        logger.info("Запуск Dzen News Scraper...")
        
        try:
            # Инициализация браузера
            await self.init_browser()
            
            # Создаем страницу для сбора карточек
            page = await self.create_stealth_page()
            
            # Собираем карточки новостей
            news_items = await self.get_news_cards(page)
            await page.close()
            
            if not news_items:
                logger.error("Не удалось получить новости. Проверьте селекторы или защиту сайта.")
                return
            
            # Ограничиваем количество статей
            news_items = news_items[:max_articles]
            
            # Собираем полный контент
            full_articles = await self.scrape_full_articles(news_items)
            
            # Сохраняем результаты
            await self.save_results(full_articles, save_format)
            
            self.collected_articles = full_articles
            logger.info(f"Скрапинг завершен успешно. Собрано {len(full_articles)} статей.")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при работе скрапера: {e}")
        
        finally:
            if self.browser:
                await self.browser.close()


async def main():
    """Основная функция запуска"""
    scraper = DzenNewsScraper()
    
    # Настройки запуска
    max_articles = 20  # Максимальное количество статей для сбора
    save_format = 'json'  # 'json' или 'markdown'
    
    await scraper.run_scraper(max_articles, save_format)
    
    # Дополнительно сохраняем в markdown
    if scraper.collected_articles:
        await scraper.save_results(scraper.collected_articles, 'markdown')


if __name__ == "__main__":
    asyncio.run(main())