import sqlite3


def init_db():
    """
    Инициализация базы данных. Создание таблицы для манги и файлов.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    # Таблица для манги
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manga (
            id INTEGER PRIMARY KEY,
            author_name TEXT,
            author_id TEXT,
            manga_title TEXT,
            manga_url TEXT,
            tags TEXT
        )
    ''')

    # Таблица для файлов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS downloaded_files (
            id INTEGER PRIMARY KEY,
            manga_id INTEGER,
            file_url TEXT,
            FOREIGN KEY (manga_id) REFERENCES manga (id)
        )
    ''')

    conn.commit()
    conn.close()


def save_manga_info(author_name, author_id, manga_title, manga_url, tags):
    """
    Сохраняет информацию о манге в базу данных. Если манга уже существует, то ничего не делает.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO manga (author_name, author_id, manga_title, manga_url, tags)
        VALUES (?, ?, ?, ?, ?)
    ''', (author_name, author_id, manga_title, manga_url, ','.join(tags)))
    conn.commit()
    conn.close()


def save_file_info(manga_id, file_url):
    """
    Сохраняет информацию о файле в базу данных. Если файл уже существует, то ничего не делает.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO downloaded_files (manga_id, file_url) VALUES (?, ?)', (manga_id, file_url))
    conn.commit()
    conn.close()


def is_manga_downloaded(url_manga):
    """
    Проверяет, существует ли манга в базе данных. Если существует, возвращает True, иначе False.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    cursor.execute('SELECT EXISTS(SELECT 1 FROM manga WHERE manga_url=? LIMIT 1)', (url_manga,))
    exists = cursor.fetchone()[0]

    conn.close()
    return exists == 1


def is_file_downloaded(file_url):
    """
    Проверяет, существует ли файл в базе данных. Если существует, возвращает True, иначе False.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    cursor.execute('SELECT EXISTS(SELECT 1 FROM downloaded_files WHERE file_url=? LIMIT 1)', (file_url,))
    exists = cursor.fetchone()[0]

    conn.close()
    return exists == 1
