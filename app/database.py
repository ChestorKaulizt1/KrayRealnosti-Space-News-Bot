import sqlite3
from pathlib import Path


DATABASE_PATH = "data/news.db"


def get_connection():
    Path(DATABASE_PATH).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            published TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    return connection


def article_exists(url: str) -> bool:
    connection = get_connection()

    cursor = connection.execute(
        """
        SELECT 1
        FROM articles
        WHERE url = ?
        LIMIT 1
        """,
        (url,)
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None


def save_article(
    source: str,
    title: str,
    url: str,
    published: str = ""
):
    connection = get_connection()

    connection.execute(
        """
        INSERT OR IGNORE INTO articles
        (source, title, url, published)
        VALUES (?, ?, ?, ?)
        """,
        (
            source,
            title,
            url,
            published
        )
    )

    connection.commit()
    connection.close()
