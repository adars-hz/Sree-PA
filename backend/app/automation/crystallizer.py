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
from .desktop_control import desktop_control
from .screen_share import screen_share
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

        # 3B. Screen Sharing & Screenshot Commands
        if re.search(r"\b(?:take\s+a\s+screenshot|capture\s+(?:the\s+)?screen|screenshot)\b", clean):
            res = screen_share.save_screenshot_to_disk()
            if res.get("success"):
                return f"Screenshot captured and saved to {res.get('filename')}."
            return "Captured desktop screenshot."

        if re.search(r"\b(?:share\s+(?:my\s+)?screen|open\s+screen\s+share|show\s+(?:my\s+)?screen)\b", clean):
            return "Opening Live Desktop Screen Share feed."

        # 3C. Desktop Navigation & Window Control Shortcuts
        if re.search(r"\b(?:minimize\s+all(?:\s+windows)?|show\s+desktop|go\s+to\s+desktop)\b", clean):
            desktop_control.execute_system_action("minimize_all")
            return "Minimized all windows."

        if re.search(r"\b(?:switch\s+window|next\s+window|alt\s+tab)\b", clean):
            desktop_control.execute_system_action("switch_window")
            return "Switched active window."

        if re.search(r"\b(?:close\s+active\s+window|close\s+this\s+window|close\s+window)\b", clean):
            desktop_control.execute_system_action("close_window")
            return "Closed active window."

        if re.search(r"\b(?:volume\s+up|increase\s+volume)\b", clean):
            desktop_control.execute_system_action("volume_up")
            return "Volume increased."

        if re.search(r"\b(?:volume\s+down|decrease\s+volume|lower\s+volume)\b", clean):
            desktop_control.execute_system_action("volume_down")
            return "Volume decreased."

        if re.search(r"\b(?:mute\s+audio|mute\s+sound|mute\s+volume|unmute)\b", clean):
            desktop_control.execute_system_action("mute")
            return "Muted audio."

        if re.search(r"\b(?:scroll\s+down)\b", clean):
            desktop_control.scroll(-6)
            return "Scrolled down."

        if re.search(r"\b(?:scroll\s+up)\b", clean):
            desktop_control.scroll(6)
            return "Scrolled up."

        if re.search(r"\b(?:lock\s+my\s+pc|lock\s+(?:the\s+)?computer|lock\s+workstation|lock\s+screen)\b", clean):
            desktop_control.execute_system_action("lock_pc")
            return "Locked Windows workstation."

        # Mouse and typing commands
        if clean in ("click", "left click", "mouse click"):
            desktop_control.click()
            return "Clicked."

        if clean in ("double click", "double-click"):
            desktop_control.double_click()
            return "Double clicked."

        if clean in ("right click", "right-click", "context menu"):
            desktop_control.right_click()
            return "Right clicked."

        if re.search(r"\b(?:copy(?:\s+this|\s+that|\s+selection)?)\b", clean):
            desktop_control.execute_system_action("copy")
            return "Copied to clipboard."

        if re.search(r"\b(?:paste(?:\s+this|\s+that|\s+clipboard)?)\b", clean):
            desktop_control.execute_system_action("paste")
            return "Pasted from clipboard."

        type_match = re.match(r"^(?:type|write|input)\s+[\"']?(.+?)[\"']?$", clean)
        if type_match:
            text_to_type = type_match.group(1).strip()
            if text_to_type:
                desktop_control.type_text(text_to_type)
                return f"Typed: {text_to_type}"

        press_match = re.match(r"^(?:press|hit|tap)\s+(enter|return|escape|esc|backspace|tab|space|spacebar|up|down|left|right)$", clean)
        if press_match:
            k = press_match.group(1)
            key_map = {"return": "enter", "spacebar": "space"}
            target_key = key_map.get(k, k)
            desktop_control.press_key(target_key)
            return f"Pressed {target_key}."

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
