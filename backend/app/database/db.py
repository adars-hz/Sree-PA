"""
SQLAlchemy Database Layer for Project SREE
Transitioned from raw sqlite3 to SQLAlchemy for better maintainability and Alembic migrations.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from ..core.config import settings
from ..core.logger import logger

# Base class for models
Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    model = Column(String)
    tokens = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.current_timestamp())

class Memory(Base):
    __tablename__ = 'memories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String, default='general')
    key = Column(String, nullable=False, unique=True)
    value = Column(Text, nullable=False)
    approved = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class Note(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    tags = Column(String, default='')
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class Reminder(Base):
    __tablename__ = 'reminders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text, default='')
    due_time = Column(String)
    priority = Column(String, default='normal')
    completed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())

class UserSetting(Base):
    __tablename__ = 'user_settings'
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create SQLAlchemy engine
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False}
        )

        # Configure SQLite for performance (WAL mode)
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.execute(text("PRAGMA foreign_keys=ON;"))
            conn.commit()

        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def get_session(self) -> Session:
        return self.SessionLocal()

    # --- Conversation Operations ---
    def save_message(self, session_id: str, role: str, content: str, model: str = "", tokens: int = 0) -> int:
        with self.get_session() as session:
            msg = Conversation(session_id=session_id, role=role, content=content, model=model, tokens=tokens)
            session.add(msg)
            session.commit()
            session.refresh(msg)
            return msg.id

    def get_conversation_history(self, session_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            history = session.query(Conversation)\
                .filter(Conversation.session_id == session_id)\
                .order_by(Conversation.id.asc())\
                .limit(limit).all()
            return [
                {"role": m.role, "content": m.content, "model": m.model, "created_at": m.created_at}
                for m in history
            ]

    def clear_conversation(self, session_id: str = "default"):
        with self.get_session() as session:
            session.query(Conversation).filter(Conversation.session_id == session_id).delete()
            session.commit()

    # --- Long-term Memory Operations ---
    def add_memory(self, key: str, value: str, category: str = "general") -> int:
        with self.get_session() as session:
            memory = session.query(Memory).filter(Memory.key == key).first()
            if memory:
                memory.value = value
                memory.category = category
            else:
                memory = Memory(key=key, value=value, category=category)
                session.add(memory)
            session.commit()
            session.refresh(memory)
            return memory.id

    def get_all_memories(self, approved_only: bool = True) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            query = session.query(Memory)
            if approved_only:
                query = query.filter(Memory.approved == True)
            memories = query.order_by(Memory.id.desc()).all()
            return [
                {"id": m.id, "category": m.category, "key": m.key, "value": m.value,
                 "approved": m.approved, "created_at": m.created_at, "updated_at": m.updated_at}
                for m in memories
            ]

    def delete_memory(self, memory_id: int) -> bool:
        with self.get_session() as session:
            memory = session.query(Memory).filter(Memory.id == memory_id).first()
            if memory:
                session.delete(memory)
                session.commit()
                return True
            return False

    # --- Notes Operations ---
    def create_note(self, title: str, content: str, tags: str = "") -> int:
        with self.get_session() as session:
            note = Note(title=title, content=content, tags=tags)
            session.add(note)
            session.commit()
            session.refresh(note)
            return note.id

    def get_notes(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            query = session.query(Note)
            if search:
                s_term = f"%{search}%"
                query = query.filter(
                    (Note.title.like(s_term)) |
                    (Note.content.like(s_term)) |
                    (Note.tags.like(s_term))
                )
            notes = query.order_by(Note.updated_at.desc()).all()
            return [
                {"id": n.id, "title": n.title, "content": n.content, "tags": n.tags,
                 "created_at": n.created_at, "updated_at": n.updated_at}
                for n in notes
            ]

    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        return self.get_notes(search=query)

    get_all_notes = get_notes

    def update_note(self, note_id: int, title: str, content: str, tags: str = "") -> bool:
        with self.get_session() as session:
            note = session.query(Note).filter(Note.id == note_id).first()
            if note:
                note.title = title
                note.content = content
                note.tags = tags
                session.commit()
                return True
            return False

    def delete_note(self, note_id: int) -> bool:
        with self.get_session() as session:
            note = session.query(Note).filter(Note.id == note_id).first()
            if note:
                session.delete(note)
                session.commit()
                return True
            return False

    # --- Reminders Operations ---
    def create_reminder(self, title: str, due_time: str = "", priority: str = "normal", description: str = "") -> int:
        with self.get_session() as session:
            rem = Reminder(title=title, description=description, due_time=due_time, priority=priority)
            session.add(rem)
            session.commit()
            session.refresh(rem)
            return rem.id

    def get_reminders(self, include_completed: bool = True) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            query = session.query(Reminder)
            if not include_completed:
                query = query.filter(Reminder.completed == False)
            reminders = query.order_by(Reminder.completed.asc(), Reminder.id.desc()).all()
            return [
                {"id": r.id, "title": r.title, "description": r.description, "due_time": r.due_time,
                 "priority": r.priority, "completed": r.completed, "created_at": r.created_at}
                for r in reminders
            ]

    get_all_reminders = get_reminders

    def toggle_reminder(self, reminder_id: int, completed: bool) -> bool:
        with self.get_session() as session:
            rem = session.query(Reminder).filter(Reminder.id == reminder_id).first()
            if rem:
                rem.completed = completed
                session.commit()
                return True
            return False

    def delete_reminder(self, reminder_id: int) -> bool:
        with self.get_session() as session:
            rem = session.query(Reminder).filter(Reminder.id == reminder_id).first()
            if rem:
                session.delete(rem)
                session.commit()
                return True
            return False

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
        with self.get_session() as session:
            session.query(Conversation).delete()
            session.query(Memory).delete()
            session.query(Note).delete()
            session.query(Reminder).delete()
            session.commit()

# Global database manager instance
db_manager = DatabaseManager()
