import sqlite3
import os
from typing import Optional, Tuple, List

DB_NAME = 'weather_bot.db'

def get_db_connection():
    """Создает и возвращает соединение с базой данных"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализирует базу данных"""
    try:
        with get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    city TEXT NOT NULL,
                    time TEXT NOT NULL
                )
            ''')
    except sqlite3.Error as e:
        print(f"Ошибка при инициализации БД: {e}")

def save_user(chat_id: int, city: str, time: str) -> bool:
    """Сохраняет или обновляет пользователя"""
    try:
        with get_db_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO users (chat_id, city, time)
                VALUES (?, ?, ?)
            ''', (chat_id, city, time))
            return True
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении пользователя {chat_id}: {e}")
        return False

def get_user(chat_id: int) -> Optional[Tuple[str, str]]:
    """Возвращает данные пользователя"""
    try:
        with get_db_connection() as conn:
            row = conn.execute('''
                SELECT city, time FROM users WHERE chat_id = ?
            ''', (chat_id,)).fetchone()
            return (row['city'], row['time']) if row else None
    except sqlite3.Error as e:
        print(f"Ошибка при получении пользователя {chat_id}: {e}")
        return None

def get_all_users() -> List[Tuple[int, str, str]]:
    """Возвращает всех пользователей"""
    try:
        with get_db_connection() as conn:
            return conn.execute('''
                SELECT chat_id, city, time FROM users
            ''').fetchall()
    except sqlite3.Error as e:
        print(f"Ошибка при получении всех пользователей: {e}")
        return []

def delete_user(chat_id: int) -> bool:
    """Удаляет пользователя"""
    try:
        with get_db_connection() as conn:
            conn.execute('''
                DELETE FROM users WHERE chat_id = ?
            ''', (chat_id,))
            return True
    except sqlite3.Error as e:
        print(f"Ошибка при удалении пользователя {chat_id}: {e}")
        return False