import requests

import re
import os
import logging
import sys

from DB import init_db, save_manga_info, save_file_info, is_manga_downloaded, is_file_downloaded
from utils import make_request, clean_filename, extract_domain, rm_prefix, HEADERS, setup_logging


def readfile(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and 'mangaka' in line:
                    author(line)
                elif line and 'manga' in line:
                    manga(line)
    except Exception as e:
        logging.error(f"Ошибка при чтении файла: {e}")


def author(url_author):
    list_titles = []

    count = 0
    has_titles = True

    site = extract_domain(url_author)

    # Парсинг страницы автора
    logging.info(f'Парсинг страницы автора: {url_author}')
    try:
        while has_titles:
            url = f"{url_author}?offset={count}"
            soup = make_request(url)

            titles = soup.select('a[class="title_link"]')
            if not titles:
                break

            for title in titles:
                href = title.get('href')
                full_url = f"{site}{href}" if 'manga-chan.me' in url_author \
                    else f"{site}{href}"
                list_titles.append(full_url)

            count += 20

        logging.info(f'Найдено {len(list_titles)} манг')

    except Exception as e:
        logging.error(f"Ошибка при парсинге страницы автора: {e}")
        return

    logging.info(f'Парсинг страницы автора завершена успешно')

    # Обработка каждой ссылки манги
    logging.info(f'Парсинг всех манг этого автора')
    try:
        for title_url in list_titles:
            manga(title_url)
    except Exception as e:
        logging.error(f"Ошибка при парсинге манги: {e}")
    logging.info(f'Парсинг всех манг этого автора завершен')


def manga(url_manga):
    logging.info(f'Парсинг манги: {url_manga}')

    # Проверка на наличие манги в базе данных
    if is_manga_downloaded(url_manga):
        logging.info(f"Манга уже скачана")
        return

    try:
        soup = make_request(url_manga)
    except Exception as e:
        logging.error(f"Ошибка при парсинге страницы манги: {e}")
        return

    # Извлечение названия манги и автора
    manga_title_tag = soup.find('a', class_='title_top_a')
    if manga_title_tag:
        manga_title = manga_title_tag.get_text(strip=True)
    else:
        logging.error(f"Не удалось извлечь название манги")
        return
    logging.info(f'Название манги: {manga_title}')

    author_tag = soup.find('a', href=re.compile(r"/mangaka/\d+/"))
    if author_tag:
        author_name = author_tag.get_text(strip=True)
    else:
        logging.error(f"Не удалось извлечь автора манги")
        return
    author_id = re.search(r"/mangaka/(\d+)/", author_tag['href']).group(1) if author_tag else None

    # Извлечение тегов
    tag_elements = soup.select('li.sidetag > a:last-child')
    tag_names = [tag.get_text() for tag in tag_elements] if tag_elements else []

    manga_info = (f'Название: {manga_title}\nАвтор: {author_name}\n'
                  f'ID автора: {author_id}\nТэги: {tag_names}\nСсылка: {url_manga}')

    # Создание пути для сохранения файла
    manga_title = clean_filename(manga_title)
    author_name = clean_filename(author_name)
    save_path = os.path.join(author_name, manga_title)

    # Создание пути для сохранения файла
    try:
        os.makedirs(save_path, exist_ok=True)
    except OSError as e:
        logging.error(f"Ошибка при создании директории с мангой: {e}")
        return

    # Сохранение обложки
    logging.info(f'Поиск обложки')
    cover_img_tag = soup.find('img', id='cover')
    if cover_img_tag and cover_img_tag.has_attr('src') and cover_img_tag['src'] != '':
        cover_img_url = cover_img_tag['src']
        # Скачивание и сохранение изображения
        try:
            response = requests.get(cover_img_url)
            if response.status_code == 200:
                with open(os.path.join(save_path, 'cover.jpg'), 'wb') as file:
                    file.write(response.content)
                logging.info(f'Обложка успешно скачана')
            else:
                logging.warning(f"Обложка не найдена")
        except Exception as e:
            logging.warning(f"Ошибка при скачивании обложки для манги: {e}")
    else:
        logging.warning(f"Обложка не найдена")

    # Сохранение информации в текстовый файл
    logging.info(f'Сохранение информации о манге')
    try:
        with open(os.path.join(save_path, 'info.txt'), 'w', encoding='utf-8') as file:
            file.write(manga_info)
        logging.info(f'Информация о манге успешно сохранена')
    except Exception as e:
        logging.error(f"Ошибка при сохранении информации о манге: {e}")

    # Смена URL для скачивания
    logging.info(f'Скачивание манги')
    url_download = re.sub(r"(https://)(.*?)(/manga/)", r"\1\2/download/", url_manga)
    try:
        download(url_download, directory=save_path)

        # Сохранение информации о манге в базу данных
        logging.info(f'Сохранение информации о манге в базу данных')
        save_manga_info(author_name, author_id, manga_title, url_manga, tag_names)
        logging.info(f'Информация о манге успешно сохранена в базу данных')
    except Exception as e:
        logging.error(f"Ошибка при скачивании манги: {e}")
        try:
            with open('error.txt', 'a', encoding='utf-8') as file:
                file.write(url_manga + '\n')
        except Exception as e:
            logging.error(f"Ошибка при записи ошибки в файл: {e}")
        return
    logging.info(f'Скачивание манги завершено успешно')


def download(url_download, directory):
    """
    Скачивает файлы по указанным URL и сохраняет их в указанной директории.
    """
    logging.info(f'Парсинг страницы скачивания: {url_download}')
    try:
        soup = make_request(url_download)
    except Exception as e:
        logging.error(f"Ошибка при парсинге страницы скачивания: {e}")
        return
    logging.info(f'Парсинг страницы скачивания завершен успешно')

    # Находим все ссылки для скачивания
    download_links = soup.select('#download_table a[href]')

    # Скачивание файлов
    logging.info(f'Найдено {len(download_links)} файлов')
    for link in download_links:
        download_url = link['href']
        filename = link.get_text()

        # Извлечение manga_id из URL
        manga_id_match = re.search(r'id=(\d+)', download_url)
        if not manga_id_match:
            logging.error(f"Не удалось извлечь manga_id из URL: {download_url}")
            return
        manga_id = int(manga_id_match.group(1))

        if is_file_downloaded(download_url):
            logging.info(f"Файл уже скачан: {download_url}")
            continue

        # Скачивание файла
        logging.info(f'Скачивание файла: {filename}')
        try:
            response = requests.get(download_url, headers=HEADERS)
        except Exception as e:
            logging.error(f"Ошибка при скачивании файла: {e}")
            raise Exception(f"Ошибка при скачивании файла: {e}")

        if response.status_code == 200:
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'wb') as file:
                    file.write(response.content)
            except Exception as e:
                logging.error(f"Ошибка при сохранении файла: {e}")
                raise Exception(f"Ошибка при сохранении файла: {e}")

            logging.info(f'Файл {filename} успешно скачан')
            save_file_info(manga_id, download_url)
        else:
            logging.error(f'Ошибка при скачивании файла: {filename}')
            raise Exception(f'Ошибка при скачивании файла: {filename}')

    logging.info(f'Скачивание файлов завершено')


def main():
    """
    В зависимости от того, какая ссылка подается, вызывается соответствующая функция.
    """
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print('Enter link to author or manga')
        url = input()
    url = rm_prefix(url)

    init_db()

    if '/mangaka/' in url:
        author(url)
    elif '/manga/' in url:
        manga(url)

    elif 'file' in url:
        print('Enter path to file')
        url = input()
        readfile(url)

    else:
        logging.error('Incorrect link')


if __name__ == '__main__':
    setup_logging()
    main()
