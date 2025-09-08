rss = '''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>AINews RSS — Главное</title>
  <link>https://dzen.ru/news</link>
  <description>Главные новости России и мира. Автообновление GitHub Actions.</description>
  <item>
    <title>Автоматически обновляемый тестовый пост</title>
    <link>https://example.com/test-news</link>
    <pubDate>Mon, 08 Sep 2025 19:37:59 +0300</pubDate>
    <description><![CDATA[Это автоматический тестовый пост.]]></description>
  </item>
</channel>
</rss>'''
with open('feed_main.xml', 'w', encoding='utf-8') as f:
    f.write(rss)
