import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.logging_config import logger

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bunny.db')

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                external_chat_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(source, external_chat_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                level INTEGER NOT NULL,
                result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        ''')

def get_or_create_conversation(source: str, external_chat_id: str) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM conversations WHERE source = ? AND external_chat_id = ?', (source, external_chat_id))
        row = cursor.fetchone()
        if row:
            return row['id']
        
        now = datetime.utcnow().isoformat()
        cursor.execute(
            'INSERT INTO conversations (source, external_chat_id, created_at, updated_at) VALUES (?, ?, ?, ?)',
            (source, external_chat_id, now, now)
        )
        return cursor.lastrowid

def add_message(conversation_id: int, role: str, content: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute(
            'INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)',
            (conversation_id, role, content, now)
        )
        cursor.execute(
            'UPDATE conversations SET updated_at = ? WHERE id = ?',
            (now, conversation_id)
        )

def get_recent_messages(conversation_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?',
            (conversation_id, limit)
        )
        rows = cursor.fetchall()
        # Return oldest first
        return [dict(row) for row in reversed(rows)]

def create_task(conversation_id: int, description: str, level: int = 1) -> int:
    if level not in (1, 2):
        raise ValueError("Task level must be 1 or 2.")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute(
            'INSERT INTO tasks (conversation_id, description, status, level, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
            (conversation_id, description, 'PENDING', level, now, now)
        )
        return cursor.lastrowid

def update_task_status(task_id: int, status: str, result: Optional[str] = None) -> None:
    valid_statuses = ('PENDING', 'RUNNING', 'WAITING', 'DONE', 'FAILED', 'BLOCKED')
    if status not in valid_statuses:
        raise ValueError(f"Status must be one of {valid_statuses}")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        if result is not None:
            cursor.execute(
                'UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?',
                (status, result, now, task_id)
            )
        else:
            cursor.execute(
                'UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?',
                (status, now, task_id)
            )
        logger.info(f"Task {task_id} status updated to {status}")

def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def get_tasks(conversation_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE conversation_id = ? ORDER BY created_at DESC', (conversation_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

