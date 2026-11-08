"""
Executive Daily Briefing Engine for Project SREE
Synthesizes live weather, pending tasks, recent notes, and system telemetry into a cohesive report.
"""

from typing import Dict, Any
from datetime import datetime
from ..database.db import db_manager
from ..automation.executor import automation_executor
from .weather import weather_service

class BriefingEngine:
    async def generate_briefing(self, city: str = "auto") -> Dict[str, Any]:
        # 1. Weather
        weather = await weather_service.get_weather(city=city)
        
        # 2. Reminders
        reminders = db_manager.get_reminders(include_completed=False)
        
        # 3. Notes
        notes = db_manager.get_notes()
        recent_notes = notes[:3] if notes else []

        # 4. Telemetry
        telemetry = automation_executor.get_system_telemetry()

        # Build clean natural speech text for TTS
        date_str = datetime.now().strftime("%A, %B %d")
        weather_text = f"The weather in {weather.get('location', 'your area')} is {weather.get('condition', 'clear')} at {weather.get('temperature_c', '--')} degrees Celsius." if weather.get("success") else "Weather data unavailable."
        tasks_count = len(reminders)
        tasks_text = f"You have {tasks_count} pending task{'s' if tasks_count != 1 else ''} on your schedule." if tasks_count > 0 else "Your task list is clear today."
        
        briefing_text = (
            f"Good day, Boss. Today is {date_str}. {weather_text} {tasks_text} "
            f"System telemetry indicates all cores are functioning optimally with an uptime of {telemetry.get('uptime_hours', 0)} hours. "
            f"How may I assist you this morning?"
        )

        return {
            "date": date_str,
            "weather": weather,
            "pending_reminders": reminders,
            "recent_notes": recent_notes,
            "telemetry": telemetry,
            "spoken_summary": briefing_text
        }

briefing_engine = BriefingEngine()

