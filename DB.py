import sqlite3


def init_db():
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()


def save_manga_info(author_name, author_id, manga_title, manga_url, tags):
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO manga (author_name, author_id, manga_title, manga_url, tags)
        VALUES (?, ?, ?, ?, ?)
    ''', (author_name, author_id, manga_title, manga_url, ','.join(tags)))
    conn.commit()
    conn.close()


def is_manga_downloaded(url_manga):
    conn = sqlite3.connect('manga.db')
    cursor = conn.cursor()

    cursor.execute('SELECT EXISTS(SELECT 1 FROM manga WHERE manga_url=? LIMIT 1)', (url_manga,))
    exists = cursor.fetchone()[0]

    conn.close()
    return exists == 1
