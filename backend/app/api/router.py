"""
Main API Router for SREE Assistant
Integrates system telemetry, AI chat, personal memory, notes, reminders,
automation, web search, and security endpoints.
"""

from fastapi import APIRouter
from .system import router as system_router
from .chat import router as chat_router
from .memory import router as memory_router
from .notes import router as notes_router
from .reminders import router as reminders_router
from .automation import router as automation_router
from .search import router as search_router
from .data import router as data_router

api_router = APIRouter()

api_router.include_router(system_router)
api_router.include_router(chat_router)
api_router.include_router(memory_router)
api_router.include_router(notes_router)
api_router.include_router(reminders_router)
api_router.include_router(automation_router)
api_router.include_router(search_router)
api_router.include_router(data_router)
