import sqlite3


def init_db():
    """
    Инициализация базы данных. Создание таблиц для манги, серий, циклов/групп, переводчиков и тэгов.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    # Таблица для серий или оригинальных работ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')

    # Таблица для циклов/групп
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groupes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')

    # Таблица для переводчиков
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS translators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')

    # Таблица для тэгов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')

    # Таблица для манги
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manga (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            series_id INTEGER,
            cycle_id INTEGER,
            translator_id INTEGER,
            upload_date TEXT,
            description TEXT,
            tags TEXT,
            chapter_count INTEGER,
            upload_successful BOOLEAN,
            FOREIGN KEY (series_id) REFERENCES series (id),
            FOREIGN KEY (cycle_id) REFERENCES cycles (id),
            FOREIGN KEY (translator_id) REFERENCES translators (id)
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


def save_manga_info(title, author, series, cycle, translator, upload_date, description, tags, chapter_count, upload_successful):
    """
    Сохраняет информацию о манге в базу данных. Если манга уже существует, то ничего не делает.
    """
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    # Вставка или получение id для серии
    cursor.execute('''
        INSERT OR IGNORE INTO series (name) VALUES (?)
    ''', (series,))
    cursor.execute('SELECT id FROM series WHERE name = ?', (series,))
    series_id = cursor.fetchone()[0]

    # Вставка или получение id для цикла/группы
    cursor.execute('''
        INSERT OR IGNORE INTO cycles (name) VALUES (?)
    ''', (cycle,))
    cursor.execute('SELECT id FROM cycles WHERE name = ?', (cycle,))
    cycle_id = cursor.fetchone()[0]

    # Вставка или получение id для переводчика
    cursor.execute('''
        INSERT OR IGNORE INTO translators (name) VALUES (?)
    ''', (translator,))
    cursor.execute('SELECT id FROM translators WHERE name = ?', (translator,))
    translator_id = cursor.fetchone()[0]

    # Вставка информации о манге
    cursor.execute('''
        INSERT INTO manga (title, author, series_id, cycle_id, translator_id, upload_date, description, tags, chapter_count, upload_successful)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, author, series_id, cycle_id, translator_id, upload_date, description, tags, chapter_count, upload_successful))

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

    cursor.execute('SELECT EXISTS(SELECT 1 FROM manga WHERE title=? LIMIT 1)', (title,))
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


if __name__ == '__main__':
    init_db()
