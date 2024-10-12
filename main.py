import requests

import re
import os
import logging
import sys

from concurrent.futures import ThreadPoolExecutor, as_completed

from DB import init_db, save_manga_info, save_file_info, is_manga_downloaded, is_file_downloaded
from utils import make_request, clean_filename, extract_domain, rm_prefix, HEADERS, setup_logging, get_manga_id


def process_line(line: str) -> None:
    """
    Обработка ссылки. Вызывает функцию для обработки строки в зависимости от ее содержимого.

    :param line: Ссылка на страницу автора или манги
    :return: None
    """
    try:
        line = line.strip()
        if line and 'mangaka' in line:
            author(line)
        elif line and 'manga' in line:
            manga(line)
    except Exception as e:
        logging.error(f"Ошибка при обработке строки: {e}")


def readfile_parallel(path: str) -> None:
    """
    Чтение файла и параллельная обработка строк.

    :param path: Путь к файлу
    :return: None
    """
    try:
        with open(path, 'r', encoding='utf-8') as file:
            # Создание списка всех строк файла
            lines = file.readlines()

        # Использование ThreadPoolExecutor для параллельной обработки строк
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Запуск задачи обработки для каждой строки
            futures = [executor.submit(process_line, line) for line in lines]

            # Ожидание завершения всех задач
            '''for future in as_completed(futures):
                try:
                    # Получение результата выполнения задачи, если необходимо
                    result = future.result()
                    pass
                except Exception as e:
                    logging.error(f"Ошибка при выполнении задачи: {e}")'''
    except Exception as e:
        logging.error(f"Ошибка при чтении файла: {e}")


def author(url_author: str) -> None:
    """
    Парсинг страницы автора. Извлекает все манги автора и загружает их.

    :param url_author: Ссылка на страницу автора
    :return: None
    """
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
        try:
            with open('error.txt', 'a', encoding='utf-8') as file:
                file.write(url_author + '\n')
        except Exception as e:
            logging.error(f"Ошибка при записи ошибки в файл: {e}")
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

    try:
        with open('done.txt', 'a', encoding='utf-8') as file:
            file.write(url_author + '\n')
    except Exception as e:
        logging.error(f"Ошибка при записи в файл: {e}")
    logging.info(f'Запись в файл "done.txt" завершена')


def manga(url_manga: str) -> None:
    """
    Парсинг манги по указанной ссылке. Скачивает мангу и создает директорию с информацией о манге.
    Сохраняет информацию о манге в базу данных.

    :param url_manga: Ссылка на мангу
    :return: None
    """
    logging.info(f'Парсинг манги: {url_manga}')

    # Проверка на наличие манги в базе данных
    if is_manga_downloaded(url_manga):
        logging.info(f"Манга уже скачана")
        return

    try:
        soup = make_request(url_manga)
    except Exception as e:
        logging.error(f"Ошибка при парсинге страницы манги: {e}")
        try:
            with open('error.txt', 'a', encoding='utf-8') as file:
                file.write(url_manga + '\n')
        except Exception as e:
            logging.error(f"Ошибка при записи ошибки в файл: {e}")
        return

    # Извлечение названия манги и автора
    manga_title_tag = soup.find('a', class_='title_top_a')
    if manga_title_tag:
        manga_title = manga_title_tag.get_text(strip=True)
    else:
        logging.error(f"Не удалось извлечь название манги")
        try:
            with open('error.txt', 'a', encoding='utf-8') as file:
                file.write(url_manga + '\n')
        except Exception as e:
            logging.error(f"Ошибка при записи ошибки в файл: {e}")
        return
    logging.info(f'Название манги: {manga_title}')

    author_tag = soup.find('a', href=re.compile(r"/mangaka/\d+/"))
    if author_tag:
        author_name = author_tag.get_text(strip=True)
    else:
        logging.error(f"Не удалось извлечь автора манги")
        try:
            with open('error.txt', 'a', encoding='utf-8') as file:
                file.write(url_manga + '\n')
        except Exception as e:
            logging.error(f"Ошибка при записи ошибки в файл: {e}")
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
        try:
            with open('error.txt', 'a', encoding='utf-8') as file:
                file.write(url_manga + '\n')
        except Exception as e:
            logging.error(f"Ошибка при записи ошибки в файл: {e}")
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

    try:
        with open('done.txt', 'a', encoding='utf-8') as file:
            file.write(url_manga + '\n')
    except Exception as e:
        logging.error(f"Ошибка при записи в файл: {e}")
    logging.info(f'Запись в файл "done.txt" завершена')


def download(url_download: str, directory: str) -> None:
    """
    Движок скачивания файлов. Скачивает файлы по ссылке и сохраняет их в указанную директорию.

    :param url_download: Ссылка для скачивания
    :param directory: Директория для сохранения файлов
    :return: None
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
    if download_links is None or 0:
        logging.warning(f"Файлы не найдены")
        try:
            open(os.path.join(directory, 'empty.txt'), 'w').close()
        except Exception as e:
            logging.error(f"Ошибка при создании пустого файла: {e}")
        raise Exception(f"Файлы не найдены")

    logging.info(f'Найдено {len(download_links)} файлов')
    for link in download_links:
        download_url = link['href']
        filename = link.get_text()

        # Извлечение manga_id из URL
        manga_id = get_manga_id(download_url)

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
            file_path = os.path.join(directory, f'{manga_id}_{filename}')
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
    Программа для скачивания манги с сайта manga сайт.
    Проверяет, является ли введенная ссылка ссылкой на автора или мангу или вовсе на файл.
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

    else:
        readfile_parallel(url)


if __name__ == '__main__':
    setup_logging('download.log')
    main()
