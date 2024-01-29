import requests
from bs4 import BeautifulSoup

import re
import os
from pathlib import Path
import logging
import sys

from DB import init_db, save_manga_info, is_manga_downloaded

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.9",
    "Referer": "https://manga-chan.me/",
    "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/81.0.4044.141 Safari/537.36"
}


def clean_filename(filename):
    """
    Очищает имя файла от запрещенных символов.
    """
    # Список запрещенных символов в именах файлов для большинства ОС
    forbidden_chars = r'[\\/*?:"<>|]'
    return re.sub(forbidden_chars, '', filename)


def make_request(url):
    """
    Выполняет HTTP-запрос и возвращает объект BeautifulSoup.
    """
    try:
        with requests.Session() as session:
            session.headers.update(HEADERS)
            response = session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе к {url}: {e}")
        return None


def author(url_author):
    list_titles = []

    count = 0
    has_titles = True

    while has_titles:
        url = f"{url_author}?offset={count}"
        soup = make_request(url)

        titles = soup.select('a[class="title_link"]')
        if not titles:
            break

        for title in titles:
            href = title.get('href')
            full_url = f"https://manga-chan.me{href}" if 'manga-chan.me' in url_author \
                else f"https://hentaichan.live{href}"
            list_titles.append(full_url)

        count += 20

    logging.info(f'Найдено {len(list_titles)} манг')

    # Обработка каждой ссылки манги
    for title_url in list_titles:
        manga(title_url)


def manga(url_manga):
    if is_manga_downloaded(url_manga):
        logging.info(f"Манга уже скачана: {url_manga}")
        return

    soup = make_request(url_manga)

    # Извлечение названия манги и автора
    manga_title_tag = soup.find('a', class_='title_top_a')
    manga_title = manga_title_tag.get_text(strip=True) if manga_title_tag else 'Название манги не найдено'
    author_tag = soup.find('a', href=re.compile(r"/mangaka/\d+/"))
    author_name = author_tag.get_text(strip=True) if author_tag else 'Автор не найден'
    author_id = re.search(r"/mangaka/(\d+)/", author_tag['href']).group(1) if author_tag else None

    # Извлечение тегов
    tag_elements = soup.select('li.sidetag > a:last-child')
    tag_names = [tag.get_text() for tag in tag_elements]

    # Вывод информации
    manga_info = (f'Название: {manga_title}\nАвтор: {author_name}\n'
                  f'ID автора: {author_id}\nТэги: {tag_names}\nСсылка: {url_manga}')

    logging.info(f'{manga_title}')

    # Создание пути для сохранения файла
    manga_title = clean_filename(manga_title)
    author_name = clean_filename(author_name)
    save_path = Path(author_name) / manga_title

    # Сохранение обложки
    cover_img_tag = soup.find('img', id='cover')
    if cover_img_tag and cover_img_tag.has_attr('src') and cover_img_tag['src'] != '':
        # Создание пути для сохранения файла
        os.makedirs(save_path, exist_ok=True)

        cover_img_url = cover_img_tag['src']
        # Скачивание и сохранение изображения
        response = requests.get(cover_img_url)
        if response.status_code == 200:
            with open(save_path / 'cover.jpg', 'wb') as file:
                file.write(response.content)
        else:
            logging.error(f"Ошибка при загрузке обложки")
    else:
        logging.warning(f"Обложка не найдена")

    # Сохранение информации в текстовый файл
    with open(save_path / 'info.txt', 'w', encoding='utf-8') as file:
        file.write(manga_info)

    # Смена URL для скачивания
    url_download = re.sub(r"(https://)(.*?)(/manga/)", r"\1\2/download/", url_manga)
    download(url_download, directory=save_path)

    save_manga_info(author_name, author_id, manga_title, url_manga, tag_names)


def download(url_download, directory):
    soup = make_request(url_download)

    # Находим все ссылки для скачивания
    download_links = soup.select('#download_table a[href]')

    for link in download_links:
        download_url = link['href']
        filename = link.get_text()

        # Скачивание файла
        response = requests.get(download_url, headers=HEADERS)
        if response.status_code == 200:
            with open(directory / filename, 'wb') as file:
                file.write(response.content)

            logging.info(f'Файл {filename} успешно скачан')
        else:
            logging.error(f'Ошибка при скачивании файла: {filename}')


def main():
    """
    В зависимости от того, какая ссылка подается, вызывается соответствующая функция.
    """
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print('Enter link to author or manga')
        url = input()
        print("\n")

    init_db()

    if 'hentaichan.live' in url:
        url = re.sub(r"(https://)(.*?)(hentaichan\.live)", r"\1\3", url)
    if '/mangaka/' in url:
        author(url)
    elif '/manga/' in url:
        manga(url)
    else:
        logging.error('Incorrect link')


if __name__ == '__main__':
    main()
