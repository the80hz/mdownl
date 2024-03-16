from playwright.async_api import async_playwright
import asyncio

from DB import init_db, save_manga_info, save_file_info, is_manga_downloaded, is_file_downloaded
from utils import make_request, clean_filename, extract_domain, rm_prefix, HEADERS, setup_logging, get_manga_id


async def handle_page(page):
    # Функция для обработки содержимого страницы
    # Например, скрыть определенные блоки
    titles = await page.query_selector_all('.title_link')
    print(titles)
    for title in titles:
        href = await title.get_attribute('href')
        full_url = href
        # Если URL удовлетворяет условию (пример с заглушкой функции)
        if await is_manga_downloaded(full_url):  # Функция для проверки URL
            await title.evaluate("element => element.style.display='none'")


async def monitor_new_pages(browser):
    # Функция для отслеживания создания новых страниц и вкладок
    async def handle_new_page(page):
        # Добавляем обработчик для каждой новой страницы
        await handle_page(page)
    browser.on("page", handle_new_page)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Запуск браузера в видимом режиме
        page = await browser.new_page()
        await monitor_new_pages(browser)  # Начать отслеживание новых страниц
        await page.goto('https://example.com')  # Перейти на начальную страницу
        await handle_page(page)  # Обработать начальную страницу

        # Ожидаем некоторое время или пользовательского ввода, чтобы скрипт не завершился сразу
        await asyncio.sleep(300)  # Ожидание 5 минут
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
