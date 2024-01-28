"""
mangachan downloader
"""

import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def author(url_author):
    pass


def manga(url_manga):
    request = requests.get(url_manga)
    soup = BeautifulSoup(request.text, 'html.parser')

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
    manga_info = f'Название: {manga_title}\nАвтор: {author_name}\nID автора: {author_id}\nТэги: {tag_names}\nСсылка: {url_manga}'

    print(manga_info)

    # Создание пути для сохранения файла
    save_path = Path(author_name) / manga_title

    # Сохранение обложки
    cover_img_tag = soup.find('img', id='cover')
    if cover_img_tag and cover_img_tag.has_attr('src'):
        cover_img_url = cover_img_tag['src']

        # Создание пути для сохранения файла
        os.makedirs(save_path, exist_ok=True)

        # Скачивание и сохранение изображения
        response = requests.get(cover_img_url)
        if response.status_code == 200:
            with open(save_path / 'cover.jpg', 'wb') as file:
                file.write(response.content)
        else:
            print("Ошибка при загрузке обложки")
    else:
        print("Обложка не найдена")

    # Сохранение информации в текстовый файл
    with open(save_path / 'info.txt', 'w', encoding='utf-8') as file:
        file.write(manga_info)

    # Смена URL для скачивания
    url_download = re.sub(r"(https://)(.*?)(/manga/)", r"\1\2/download/", url_manga)
    download(url_download, directory=save_path)


def download(url_download, directory):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.9",
        "Referer": "https://manga-chan.me/",
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/81.0.4044.141 Safari/537.36"
    }
    request = requests.get(url_download)
    soup = BeautifulSoup(request.text, 'html.parser')

    # Находим все ссылки для скачивания
    download_links = soup.select('#download_table a[href]')

    for link in download_links:
        download_url = link['href']
        filename = link.get_text()

        # Скачивание файла
        response = requests.get(download_url, headers=headers)
        if response.status_code == 200:
            with open(directory / filename, 'wb') as file:
                file.write(response.content)
            print(f'Файл {filename} успешно скачан')
        else:
            print(f'Ошибка при скачивании файла: {filename}')


def main():
    """
    В зависимости от того, какая ссылка подается в консоль, вызывается соответствующая функция
    :return:
    """
    print('Enter link to author or manga')
    url = input()
    print("\n")
    if 'hentaichan.live' in url:
        url = re.sub(r"(https://)(.*?)(hentaichan\.live)", r"\1\3", url)
    if '/mangaka/' in url:
        author(url)
    elif '/manga/' in url:
        manga(url)
    else:
        print('Incorrect link')


if __name__ == '__main__':
    main()
