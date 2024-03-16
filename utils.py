import logging
import re
import glob
import os

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.9",
    "Referer": "https://manga-chan.me/",
    "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/81.0.4044.141 Safari/537.36"
}


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


def clean_filename(filename):
    """
    Очищает имя файла от запрещенных символов.
    """
    # Список запрещенных символов в именах файлов для большинства ОС
    forbidden_chars = r'[\\/*?:"<>|]'
    return re.sub(forbidden_chars, '', filename)


def extract_domain(url):
    pattern = re.compile(r'https?://[^/]+')
    match = pattern.search(url)
    if match:
        return match.group()
    else:
        return url


def rm_prefix(url):
    pattern = r"https?://(?:[^/]+\.)?([^/]+\.[^/]+)/(.*?)"
    cleaned_url = re.sub(pattern, r"https://\1/\2", url)
    return cleaned_url


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Устанавливаем уровень логгирования

    # Обработчик для записи логов в файл
    file_handler = logging.FileHandler('download.log', 'a')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # Обработчик для вывода логов в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def merge_txt_files(directory, output_file):
    # Создаем множество для хранения уникальных строк
    unique_lines = set()

    # Ищем все .txt файлы в указанной директории
    for txt_file in glob.glob(os.path.join(directory, '*.txt')):
        with open(txt_file, 'r', encoding='utf-8') as file:
            for line in file:
                # Удаляем пробельные символы в начале и конце строки и добавляем строку в множество
                unique_lines.add(line.strip())

    # Записываем уникальные строки в файл вывода
    with open(output_file, 'w', encoding='utf-8') as output:
        for line in sorted(unique_lines):  # Опционально сортируем строки перед записью
            output.write(line + '\n')