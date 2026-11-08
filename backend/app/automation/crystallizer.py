"""
Skill Crystallizer Engine for Project SREE
Enables 0ms fast-path execution of cached deterministic skills and application shortcuts.
Bypasses LLM token costs for recognized intents.
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from .allowlist import ALLOWLISTED_APPLICATIONS
from .executor import automation_executor
from ..services.weather import weather_service
from ..services.briefing import briefing_engine

class SkillCrystallizer:
    def __init__(self):
        # In-memory crystallized skill cache
        self._crystallized_skills: Dict[str, Dict[str, Any]] = {}

    def crystallize_skill(self, name: str, pattern: str, handler_description: str):
        """Crystallizes a new automation macro for 0ms execution."""
        self._crystallized_skills[name] = {
            "pattern": re.compile(pattern, re.IGNORECASE),
            "description": handler_description
        }

    async def execute_fast_path(self, message: str) -> Optional[str]:
        """
        Attempts 0ms deterministic execution.
        Returns response string if handled, or None to fall back to the Agent Brain.
        """
        clean = message.lower().strip()
        
        # Strip wake prefixes (handling all phonetic variants)
        clean = re.sub(r"^(?:hey|hi|hello|ok|okay)?\s*(?:sree|sri|shree|shri|siri|three)[,\s]*", "", clean).strip()

        # 1. Greetings & Wake-Words
        if not clean or clean in ("hi", "hey", "hello", "good morning", "good afternoon", "good evening", "sree", "sri", "shree", "shri", "siri", "three"):
            hour = datetime.now().hour
            period = "morning" if hour < 12 else ("afternoon" if hour < 17 else "evening")
            return f"Hey Boss! SREE is listening. What can I do for you this {period}?"

        # 2. Deactivation Commands
        if re.search(r"\b(?:turn\s+off.*(?:voice|assistant)|stop\s+listening|deactivate.*voice|be\s+quiet|shut\s+down|go\s+to\s+sleep)\b", clean):
            return "Voice assistant deactivated. Click the Orb whenever you need me."

        # 3. Direct App Launch Shortcuts (Calculator, Notepad, Chrome, Brave, WhatsApp, VS Code, Terminal)
        launch_match = re.search(r"\b(?:open|launch|start|run)\s+(notepad|calculator|calc|explorer|browser|chrome|brave|whatsapp|terminal|cmd|taskmgr|task\s*manager|vscode|code)\b", clean)
        if launch_match:
            raw_target = launch_match.group(1).replace(" ", "")
            alias_map = {
                "notepad": "notepad",
                "calculator": "calculator",
                "calc": "calculator",
                "explorer": "explorer",
                "browser": "browser",
                "chrome": "browser",
                "brave": "browser",
                "whatsapp": "browser",
                "terminal": "terminal",
                "cmd": "terminal",
                "taskmgr": "taskmgr",
                "taskmanager": "taskmgr",
                "vscode": "vscode",
                "code": "vscode"
            }
            app_id = alias_map.get(raw_target, raw_target)
            result = automation_executor.launch_application(app_id)
            if result.get("success"):
                return f"Opening {result.get('app', app_id)}."
            return f"Notice: {result.get('error')}"

        # 4. What time is it / Current time
        if re.search(r"\b(?:what\s+time\s+is\s+it|what(?:'s|\s+is)\s+the\s+time|current\s+time)\b", clean):
            return f"It is currently {datetime.now().strftime('%I:%M %p')}."

        # 5. What is the date / Current date
        if re.search(r"\b(?:what(?:'s|\s+is)\s+(?:the\s+date|today(?:'s)?\s+date)|what\s+day\s+is\s+it)\b", clean):
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."

        # 6. Capabilities & Features
        if re.search(r"\b(?:what\s+can\s+you\s+do|capabilities|what\s+are\s+your\s+features)\b", clean):
            return "I can launch apps on your PC, check live weather, set reminders, take notes, remember your preferences, and answer any question. What would you like to do?"

        # 7. Identity & Status
        if re.search(r"\b(?:who\s+are\s+you|what\s+is\s+your\s+name)\b", clean):
            return "I am SREE, your personal AI assistant running locally and privately on your hardware."

        if re.search(r"\b(?:how\s+are\s+you|how\s+are\s+things)\b", clean):
            return "I'm functioning at peak performance and ready for your command. What's on your mind?"

        # 8. Weather Telemetry
        weather_match = re.search(r"\b(?:weather|temperature|forecast)(?:\s+(?:in|for|at)\s+([a-zA-Z\s]+))?", clean)
        if weather_match and not re.search(r"\b(?:program|code|algorithm)\b", clean):
            city = weather_match.group(1).strip() if weather_match.group(1) else "auto"
            res = await weather_service.get_weather(city=city)
            if res.get("success"):
                return (
                    f"In {res['location']}, it's currently {res['condition']} at {res['temperature_c']}°C "
                    f"(feels like {res['feels_like_c']}°C), with humidity at {res['humidity_percent']}%."
                )

        # 9. Daily Briefing
        if re.search(r"\b(?:daily|morning|today's)?\s*briefing\b|\bsummarize\s+my\s+day\b", clean):
            briefing = await briefing_engine.generate_briefing()
            return briefing["spoken_summary"]

        return None

skill_crystallizer = SkillCrystallizer()
