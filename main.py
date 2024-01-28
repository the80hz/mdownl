"""
mangachan downloader
"""

import os
import re
from urllib.parse import urljoin
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def author(url_author):
    pass


def manga(url_manga):
    request = requests.get(url_manga)
    soup = BeautifulSoup(request.text, 'html.parser')

    # Название манги
    manga_title_tag = soup.find('a', class_='title_top_a')
    manga_title = manga_title_tag.get_text() if manga_title_tag else 'Название манги не найдено'

    # Автор и его ID
    author_tag = soup.find('a', href=re.compile(r"/mangaka/\d+/"))
    if author_tag:
        author_name = author_tag.get_text()
        href = author_tag['href']
        author_id = re.search(r"/mangaka/(\d+)/", href).group(1)
    else:
        author_name = 'Автор не найден'
        author_id = None

    # Тэги
    tag_elements = soup.select('li.sidetag > a:last-child')
    tag_names = [tag.get_text() for tag in tag_elements]

    print(f'Название: {manga_title}', f'Автор: {author_name}', f'ID автора: {author_id}', f'Тэги: {tag_names}',
          f'Ссылка: {url_manga}', sep='\n')

    url_download = re.sub(r"(https://)(.*?)(/manga/)", r"\1\2/download/", url_manga)
    download(url_download)


def download(url_download):
    pass


def engine(url_dl_chapter):
    pass


def main():
    """
    В зависимости от того, какая ссылка подается в консоль, вызывается соответствующая функция
    :return:
    """
    print('Enter link to author or manga')
    url = input()
    if 'hentaichan.live' in url:
        url = re.sub(r"(https://)(.*?)(hentaichan\.live)", r"\1\3", url)
    if '/mangaka/' in url:
        author(url)
    elif '/manga/' in url:
        manga(url)
    elif '/chapter/' in url:
        download(url)
    else:
        print('Incorrect link')


if __name__ == '__main__':
    main()
