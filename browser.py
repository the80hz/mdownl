from playwright.async_api import async_playwright
import asyncio

from DB import init_db, save_manga_info, save_file_info, is_manga_downloaded, is_file_downloaded
from utils import make_request, clean_filename, extract_domain, rm_prefix, HEADERS, setup_logging, get_manga_id


async def handle_page(page):
    # Ваша логика обработки страницы
    print("Обрабатываем")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Подписываемся на событие навигации
        page.on('load', lambda frame: asyncio.create_task(handle_page(page)))
        #page.on('load', lambda: asyncio.create_task(handle_page(page)))

        await page.goto('https://google.com')
        # Пример перехода на новую страницу через клик или другое действие
        # Предположим, что есть ссылка с идентификатором link-to-click
        # await page.click('#link-to-click')

        # Чтобы скрипт не завершился сразу, ждем некоторое время или пользовательского ввода
        await asyncio.sleep(300)  # Даём 5 минут на интерактивное использование браузера

        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())