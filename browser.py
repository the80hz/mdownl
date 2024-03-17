from playwright.async_api import async_playwright
import asyncio

from DB import init_db, save_manga_info, save_file_info, is_manga_downloaded, is_file_downloaded
from utils import make_request, clean_filename, extract_domain, rm_prefix, setup_logging, get_manga_id


async def handle_page(page):
    print("Processing page...")
    print(page.url)

    content_rows = await page.query_selector_all('div[class="content_row"]')
    for content_row in content_rows:
        url = page.url
        site = extract_domain(url)
        title_link = await content_row.query_selector('a[class="title_link"]')
        href = await title_link.get_attribute('href')
        full_url = f"{site}{href}" if 'manga-chan.me' in url else f"{site}{href}"
        print(full_url)

        if is_manga_downloaded(full_url):
            await content_row.evaluate('(content_row) => content_row.style.display = "none"')
            print(f"Hidden {full_url}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        page.on('load', lambda: asyncio.create_task(handle_page(page)))

        # Corrected the URL to be a string and properly formatted.
        await page.goto("https://www.google.com")

        # Waiting for user input or a specific time before closing can be handled better with try-except.
        try:
            # Wait indefinitely until an explicit keyboard interrupt (Ctrl+C) to allow manual testing.
            await asyncio.Future()
        except KeyboardInterrupt:
            print("Script interrupted by user.")
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
