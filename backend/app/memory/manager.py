"""
Memory and Context Management Layer for SREE
Distinguishes short-term conversational context from persistent long-term memories.
"""

import re
from typing import List, Dict, Any, Optional
from ..database.db import db_manager

class MemoryManager:
    def __init__(self):
        self.db = db_manager

    def get_memory_context_string(self) -> str:
        """Constructs a clean bulleted list of approved memories to inject into LLM system prompt."""
        memories = self.db.get_all_memories(approved_only=True)
        if not memories:
            return ""
        
        lines = []
        for m in memories:
            lines.append(f"- [{m['category'].upper()}] {m['key']}: {m['value']}")
        return "\n".join(lines)

    def extract_memory_intent(self, user_message: str) -> Optional[Dict[str, str]]:
        """
        Rule-based heuristic detector to identify explicit memory requests.
        Examples:
          "Remember that my favorite language is Python"
          "Remember: I prefer concise answers"
        """
        patterns = [
            r"(?:please\s+)?remember\s*[:\-]?\s*(?:that\s+)?(.+)",
            r"(?:note\s+down\s*[:\-]?\s*(?:that\s+)?)(.+)",
            r"(?:save\s+to\s+memory\s*[:\-]?\s*)(.+)"
        ]
        
        lower_msg = user_message.strip()
        for p in patterns:
            match = re.search(p, lower_msg, re.IGNORECASE)
            if match:
                raw_fact = match.group(1).strip()
                # Split key/value if possible
                if " is " in raw_fact:
                    parts = raw_fact.split(" is ", 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                elif ":" in raw_fact:
                    parts = raw_fact.split(":", 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                else:
                    key = "preference"
                    val = raw_fact
                    
                return {"key": key, "value": val, "category": "user_preference"}
        return None

memory_manager = MemoryManager()

