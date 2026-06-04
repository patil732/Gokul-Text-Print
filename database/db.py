import sqlite3
import os
from config.settings import settings

DB_PATH = os.path.join(settings.BASE_DIR, "database", "platform.db")

def init_db():
    """
    Initializes the SQLite database and creates the users table.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('ceo', 'admin'))
        )
    ''')
    
    # Create Decision History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS decision_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            decision TEXT NOT NULL,
            confidence TEXT,
            reason TEXT
        )
    ''')
    
    conn.commit()

def get_db_connection():
    """
    Returns a connection to the SQLite database.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
