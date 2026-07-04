import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "app.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        password_hash TEXT,
        age INTEGER,
        gender TEXT,
        preferences TEXT,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]

    if "email" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN email TEXT")

    if "password_hash" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

    if "age" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN age INTEGER")

    if "gender" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN gender TEXT")

    if "preferences" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN preferences TEXT")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        content_type TEXT,
        extracted_text TEXT NOT NULL,
        summary TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()