import sqlite3


def init_db():
    """
    Инициализация базы данных. Создание таблиц для манги, авторов, серий, циклов, переводчиков и тэгов.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    # Таблица для манги
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manga (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author_id INTEGER,
            series_id INTEGER DEFAULT NULL,
            cycle_id INTEGER DEFAULT NULL,
            translator_id INTEGER,
            related_manga_ids TEXT DEFAULT NULL,
            upload_date TEXT,
            tag_ids TEXT,
            manga_url TEXT,
            cover_path TEXT DEFAULT NULL,
            FOREIGN KEY (author_id) REFERENCES authors (id),
            FOREIGN KEY (series_id) REFERENCES series (id),
            FOREIGN KEY (cycle_id) REFERENCES cycles (id),
            FOREIGN KEY (translator_id) REFERENCES translators (id)
        )
    ''')

    # Таблица для авторов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            manga_ids TEXT,
            author_url TEXT
        )
    ''')

    # Таблица для серий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            manga_ids TEXT,
            series_url TEXT
        )
    ''')

    # Таблица для циклов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            manga_ids TEXT
        )
    ''')

    # Таблица для переводчиков
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS translators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT UNIQUE,
            manga_ids TEXT,
            translator_url TEXT
        )
    ''')

    # Таблица для тэгов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            manga_ids TEXT
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


def save_author_info(author_id, name, author_url):
    """
    Сохраняет информацию об авторе в базу данных. Если автор уже существует, то ничего не делает.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO authors (id, name, author_url) VALUES (?, ?, ?)
    ''', (author_id, name, author_url))

    conn.commit()
    conn.close()


def save_manga_info_basic(manga_id, title, author_id, manga_url):
    """
    Сохраняет базовую информацию о манге в базу данных. Если манга уже существует, то ничего не делает.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO manga (id, title, author_id, manga_url) VALUES (?, ?, ?, ?)
    ''', (manga_id, title, author_id, manga_url))

    conn.commit()
    conn.close()


def is_manga_downloaded(manga_id):
    """
    Проверяет, существует ли манга в базе данных. Если существует, возвращает True, иначе False.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    cursor.execute('SELECT EXISTS(SELECT 1 FROM manga WHERE id=?)', (manga_id,))
    exists = cursor.fetchone()[0]

    conn.close()
    return exists == 1


def is_file_downloaded(file_url):
    """
    Проверяет, существует ли файл в базе данных. Если существует, возвращает True, иначе False.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    cursor.execute('SELECT EXISTS(SELECT 1 FROM downloaded_files WHERE file_url=?)', (file_url,))
    exists = cursor.fetchone()[0]

    conn.close()
    return exists == 1


if __name__ == '__main__':
    init_db()
