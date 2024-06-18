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


def save_manga_info(title, author, series, cycle, translator, related_manga_ids, upload_date, tags, manga_url,
                    cover_path):
    """
    Сохраняет информацию о манге в базу данных. Если манга уже существует, то ничего не делает.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    # Вставка или получение id для автора
    cursor.execute('''
        INSERT OR IGNORE INTO authors (name) VALUES (?)
    ''', (author,))
    cursor.execute('SELECT id, manga_ids FROM authors WHERE name = ?', (author,))
    author_row = cursor.fetchone()
    author_id = author_row[0]
    author_manga_ids = author_row[1]

    # Обновление списка манги у автора
    if author_manga_ids:
        updated_author_manga_ids = f"{author_manga_ids},{title}"
    else:
        updated_author_manga_ids = title
    cursor.execute('''
        UPDATE authors SET manga_ids = ? WHERE id = ?
    ''', (updated_author_manga_ids, author_id))

    # Вставка или получение id для серии
    if series:
        cursor.execute('''
            INSERT OR IGNORE INTO series (name) VALUES (?)
        ''', (series,))
        cursor.execute('SELECT id, manga_ids FROM series WHERE name = ?', (series,))
        series_row = cursor.fetchone()
        series_id = series_row[0]
        series_manga_ids = series_row[1]

        # Обновление списка манги в серии
        if series_manga_ids:
            updated_series_manga_ids = f"{series_manga_ids},{title}"
        else:
            updated_series_manga_ids = title
        cursor.execute('''
            UPDATE series SET manga_ids = ? WHERE id = ?
        ''', (updated_series_manga_ids, series_id))
    else:
        series_id = None

    # Вставка или получение id для цикла
    if cycle:
        cursor.execute('''
            INSERT OR IGNORE INTO cycles (name) VALUES (?)
        ''', (cycle,))
        cursor.execute('SELECT id, manga_ids FROM cycles WHERE name = ?', (cycle,))
        cycle_row = cursor.fetchone()
        cycle_id = cycle_row[0]
        cycle_manga_ids = cycle_row[1]

        # Обновление списка манги в цикле
        if cycle_manga_ids:
            updated_cycle_manga_ids = f"{cycle_manga_ids},{title}"
        else:
            updated_cycle_manga_ids = title
        cursor.execute('''
            UPDATE cycles SET manga_ids = ? WHERE id = ?
        ''', (updated_cycle_manga_ids, cycle_id))
    else:
        cycle_id = None

    # Вставка или получение id для переводчика
    cursor.execute('''
        INSERT OR IGNORE INTO translators (nickname) VALUES (?)
    ''', (translator,))
    cursor.execute('SELECT id, manga_ids FROM translators WHERE nickname = ?', (translator,))
    translator_row = cursor.fetchone()
    translator_id = translator_row[0]
    translator_manga_ids = translator_row[1]

    # Обновление списка манги у переводчика
    if translator_manga_ids:
        updated_translator_manga_ids = f"{translator_manga_ids},{title}"
    else:
        updated_translator_manga_ids = title
    cursor.execute('''
        UPDATE translators SET manga_ids = ? WHERE id = ?
    ''', (updated_translator_manga_ids, translator_id))

    # Вставка информации о манге
    cursor.execute('''
        INSERT INTO manga (title, author_id, series_id, cycle_id, translator_id, related_manga_ids, upload_date, 
        tag_ids, manga_url, cover_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        title, author_id, series_id, cycle_id, translator_id, related_manga_ids, upload_date, tags, manga_url,
        cover_path))

    manga_id = cursor.lastrowid

    # Вставка тэгов и получение их id
    for tag in tags:
        cursor.execute('''
            INSERT OR IGNORE INTO tags (name) VALUES (?)
        ''', (tag,))
        cursor.execute('SELECT id, manga_ids FROM tags WHERE name = ?', (tag,))
        tag_row = cursor.fetchone()
        tag_id = tag_row[0]
        tag_manga_ids = tag_row[1]

        # Обновление списка манги у тэга
        if tag_manga_ids:
            updated_tag_manga_ids = f"{tag_manga_ids},{title}"
        else:
            updated_tag_manga_ids = title
        cursor.execute('''
            UPDATE tags SET manga_ids = ? WHERE id = ?
        ''', (updated_tag_manga_ids, tag_id))

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


def is_manga_downloaded(title):
    """
    Проверяет, существует ли манга в базе данных. Если существует, возвращает True, иначе False.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    cursor.execute('SELECT EXISTS(SELECT 1 FROM manga WHERE title=?)', (title,))
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
