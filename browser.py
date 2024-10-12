# browser.py

from playwright.async_api import async_playwright
import asyncio

import logging

from DB import init_db, save_manga_info, save_file_info, is_manga_downloaded, is_file_downloaded
from utils import make_request, clean_filename, extract_domain, rm_prefix, setup_logging, get_manga_id


# Определите список запрещённых тегов
FORBIDDEN_TAGS = ['-']

async def handle_page(page: str) -> None:
    """
    Обработка страницы. Проверка на скачанную мангу, если true - скрыть строку с контентом
    :param page: страница
    :return: None
    """
    logging.info(f"Обработка страницы {page.url}")

    content_rows = await page.query_selector_all('div[class="content_row"]')

    hidden = 0

    for content_row in content_rows:
        logging.info(f"Обработка строки с контентом {content_row}")
        url = rm_prefix(page.url)
        site = extract_domain(url)
        title_link = await content_row.query_selector('a[class="title_link"]')
        href = await title_link.get_attribute('href')
        full_url = f"{site}{href}" if 'manga-chan.me' in url else f"{site}{href}"
        logging.info(f"Полный URL: {full_url}")

        if is_manga_downloaded(full_url):
            logging.info(f"Манга {full_url} уже скачана")
            await content_row.evaluate('(content_row) => content_row.style.display = "none"')
            hidden += 1
            logging.info(f"Строка с контентом {content_row} скрыта")

        genre_block = await content_row.query_selector('div[class="genre"]')
        a_tags = await genre_block.query_selector_all('a')
        tags = [await a_tag.inner_text() for a_tag in a_tags] if a_tags else []
        if any(tag in tags for tag in FORBIDDEN_TAGS):
            logging.info(f"Манга {full_url} содержит запрещенные теги")
            await content_row.evaluate('(content_row) => content_row.style.display = "none"')
            hidden += 1
            logging.info(f"Строка с контентом {content_row} скрыта")

    logging.info(f"Найдено {len(content_rows)} строк с контентом")
    logging.info(f"Скрыто {hidden} строк с контентом")


async def main() -> None:
    """
    Основная функция. Открывает браузер с начальной страницей google.com.
    :return: None
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        page.on('load', lambda _page: asyncio.create_task(handle_page(_page)))

        await page.goto("https://google.com")

        try:
            # Wait indefinitely until an explicit keyboard interrupt (Ctrl+C) to allow manual testing.
            await asyncio.Future()
        except KeyboardInterrupt:
            logging.info("Прерывание пользователем")
        finally:
            await browser.close()


if __name__ == '__main__':
    setup_logging('browser.log')
    init_db()
    asyncio.run(main())
