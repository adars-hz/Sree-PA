"""
SQLite Database Layer for Project SREE
Manages local-first relational storage for conversations, memory, notes, reminders, and settings.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from ..core.config import settings

logger = logging.getLogger("sree.database")

class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")  # Write-Ahead Logging for high concurrency
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def init_database(self):
        """Creates tables and indexes if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Conversations table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model TEXT,
                tokens INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);")

            # 2. Long-term memory table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT DEFAULT 'general',
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                approved INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_key ON memories(key);")

            # 3. Notes table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title);")

            # 4. Reminders & Tasks table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                due_time TEXT,
                priority TEXT DEFAULT 'normal',
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_completed ON reminders(completed);")

            # 5. User settings table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    # --- Conversation Operations ---
    def save_message(self, session_id: str, role: str, content: str, model: str = "", tokens: int = 0) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (session_id, role, content, model, tokens) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, model, tokens)
            )
            conn.commit()
            return cursor.lastrowid

    def get_conversation_history(self, session_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, model, created_at FROM conversations WHERE session_id = ? ORDER BY id ASC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_conversation(self, session_id: str = "default"):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            conn.commit()

    # --- Long-term Memory Operations ---
    def add_memory(self, key: str, value: str, category: str = "general") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (key, value, category, approved, updated_at) 
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET 
                    value = excluded.value, 
                    category = excluded.category,
                    updated_at = CURRENT_TIMESTAMP
            """, (key, value, category))
            conn.commit()
            return cursor.lastrowid

    def get_all_memories(self, approved_only: bool = True) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if approved_only:
                cursor.execute("SELECT id, category, key, value, approved, created_at, updated_at FROM memories WHERE approved = 1 ORDER BY id DESC")
            else:
                cursor.execute("SELECT id, category, key, value, approved, created_at, updated_at FROM memories ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_memory(self, memory_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- Notes Operations ---
    def create_note(self, title: str, content: str, tags: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (title, content, tags) VALUES (?, ?, ?)",
                (title, content, tags)
            )
            conn.commit()
            return cursor.lastrowid

    def get_notes(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if search:
                query = f"%{search}%"
                cursor.execute(
                    "SELECT id, title, content, tags, created_at, updated_at FROM notes WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? ORDER BY updated_at DESC",
                    (query, query, query)
                )
            else:
                cursor.execute("SELECT id, title, content, tags, created_at, updated_at FROM notes ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        return self.get_notes(search=query)

    get_all_notes = get_notes

    def update_note(self, note_id: int, title: str, content: str, tags: str = "") -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE notes SET title = ?, content = ?, tags = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, content, tags, note_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_note(self, note_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- Reminders Operations ---
    def create_reminder(self, title: str, due_time: str = "", priority: str = "normal", description: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (title, description, due_time, priority, completed) VALUES (?, ?, ?, ?, 0)",
                (title, description, due_time, priority)
            )
            conn.commit()
            return cursor.lastrowid

    def get_reminders(self, include_completed: bool = True) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if include_completed:
                cursor.execute("SELECT id, title, description, due_time, priority, completed, created_at FROM reminders ORDER BY completed ASC, id DESC")
            else:
                cursor.execute("SELECT id, title, description, due_time, priority, completed, created_at FROM reminders WHERE completed = 0 ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    get_all_reminders = get_reminders

    def toggle_reminder(self, reminder_id: int, completed: bool) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reminders SET completed = ? WHERE id = ?", (1 if completed else 0, reminder_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_reminder(self, reminder_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- Wipe & Export Operations ---
    def export_all_data(self) -> Dict[str, Any]:
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "memories": self.get_all_memories(approved_only=False),
            "notes": self.get_notes(),
            "reminders": self.get_reminders(include_completed=True),
            "conversations": self.get_conversation_history(session_id="default", limit=1000)
        }

    def wipe_all_data(self):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM conversations;")
            conn.execute("DELETE FROM memories;")
            conn.execute("DELETE FROM notes;")
            conn.execute("DELETE FROM reminders;")
            conn.commit()

# Global database manager instance
db_manager = DatabaseManager()

