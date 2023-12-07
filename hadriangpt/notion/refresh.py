from datetime import datetime
from typing import Optional
from hadriangpt.notion.api import get_all_pages, Page
from hadriangpt.bot.bot import Bot

last_refresh = None
SCRAPE_INTERVAL_SECONDS = 60 * 60


def is_within_working_hours(dt: Optional[datetime]) -> bool:
    return 8 <= dt.hour <= 18


def refresh_notion() -> list[Page]:
    global last_refresh

    if last_refresh and not is_within_working_hours(last_refresh):
        return []

    pages = get_all_pages()
    print(f"Refreshing {len(pages)} pages")
    for page in pages:
        if last_refresh is None or last_refresh < page.last_edited:
            page.scrape()

    print("refresh finished")
    last_refresh = datetime.now()
    return [page for page in pages if page.is_scraped]


def start_refresh_task(bot: Bot):
    from threading import Thread
    from time import sleep

    def refresh(bot: Bot):
        while True:
            pages = refresh_notion()
            bot.add_docs([
                {
                    'content': page.content,
                    'source': page.url
                }
                for page in pages
            ])
            sleep(60 * 60)

    Thread(target=refresh, args=(bot,)).start()
