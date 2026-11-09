"""
3-Tier Security Guard Engine for Project SREE
Strict permission gating:
  - Level 1 (Safe): Auto-execute (Calculator, Notepad, Weather, Notes, Allowlisted Apps)
  - Level 2 (Sensitive): Requires explicit voice or text confirmation ("yes" / "confirm")
  - Level 3 (Critical): Permanently blocked (formatting disks, modifying system root, raw destructive shell)
"""

import time
import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum

class SecurityLevel(Enum):
    SAFE = 1        # Level 1: Auto-execute
    SENSITIVE = 2   # Level 2: Requires explicit user confirmation
    CRITICAL = 3    # Level 3: Blocked

class SecurityGuard:
    def __init__(self):
        self._pending_action: Optional[Dict[str, Any]] = None
        self._pending_timestamp: float = 0
        self.CONFIRMATION_TIMEOUT_SEC = 60.0
        self.STRICT_MODE = False  # Set to True for higher assurance environments

    def evaluate_intent(self, intent_type: str, details: Dict[str, Any] = None) -> SecurityLevel:
        """Categorizes any action into Level 1, Level 2, or Level 3."""
        details = details or {}
        cmd = str(details.get("command", "")).lower()
        path = str(details.get("path", "")).lower()

        # Level 3: CRITICAL (Permanent Block)
        critical_patterns = [
            r"\bformat\s+[a-z]:",
            r"rmdir\s+/[sS]",
            r"del\s+/[fF]\s+/[sS]",
            r"rd\s+/[sS]\s+/[qQ]",
            r"del\s+/[fF]\s+/[sS]\s+/[qQ]",
            r"drop\s+database",
            r"system32",
            r"reg\s+delete",
            r"powershell\s+-(?:enc|e)\b",
            r"shutdown\s+/[sS]"
        ]
        for pattern in critical_patterns:
            if re.search(pattern, cmd) or re.search(pattern, path):
                return SecurityLevel.CRITICAL

        # Level 2: SENSITIVE (Requires Confirmation)
        sensitive_intents = ["wipe_data", "delete_note", "delete_memory", "kill_process", "unlisted_app"]
        if intent_type in sensitive_intents:
            return SecurityLevel.SENSITIVE

        if any(word in cmd for word in ("delete", "erase", "wipe", "remove")):
            return SecurityLevel.SENSITIVE

        # Level 1: SAFE (Auto-execute)
        return SecurityLevel.SAFE

    def stage_pending_action(self, action_type: str, payload: Dict[str, Any], prompt_message: str) -> Dict[str, Any]:
        """Holds a Level 2 action in pending state awaiting user confirmation."""
        self._pending_action = {
            "type": action_type,
            "payload": payload,
            "prompt": prompt_message,
            "created_at": time.time()
        }
        self._pending_timestamp = time.time()

        msg = f"⚠️ Security Guard Notice: {prompt_message}"
        if self.STRICT_MODE:
            msg += " Please explicitly say 'Yes, I am sure' to proceed, or 'cancel' to abort."
        else:
            msg += " Please speak or type 'yes' to proceed, or 'cancel' to abort."

        return {
            "status": "pending_confirmation",
            "security_level": 2,
            "message": msg
        }

    def check_pending_confirmation(self, user_reply: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Checks if the user's input answers a pending confirmation.
        Returns: (was_handled, executed_action, response_message)
        """
        if not self._pending_action:
            return False, None, ""

        # Check timeout
        if (time.time() - self._pending_timestamp) > self.CONFIRMATION_TIMEOUT_SEC:
            self._pending_action = None
            return False, None, "Confirmation window timed out."

        clean = user_reply.lower().strip()

        # User confirmed
        if self.STRICT_MODE:
            # Require a more specific phrase for strict mode
            if any(phrase in clean for phrase in ("yes i am sure", "i am sure", "yes proceed", "confirm proceed")):
                action = self._pending_action
                self._pending_action = None
                return True, action, "Strict confirmation verified. Executing authorized command."
            elif clean in ("yes", "confirm", "proceed"):
                # Soft confirm in strict mode - prompt again or treat as uncertain
                return False, None, "I need a bit more certainty. Please say 'Yes, I am sure' to proceed."
        else:
            # Standard confirmation
            if clean in ("yes", "confirm", "proceed", "sure", "do it", "i confirm", "yes please"):
                action = self._pending_action
                self._pending_action = None
                return True, action, "Confirmation verified. Executing authorized command."

        # User canceled
        if clean in ("no", "cancel", "abort", "stop", "nevermind", "dont"):
            self._pending_action = None
            return True, None, "Action cancelled. Operation safely aborted."

        return False, None, ""

    def has_pending_action(self) -> bool:
        if not self._pending_action:
            return False
        if (time.time() - self._pending_timestamp) > self.CONFIRMATION_TIMEOUT_SEC:
            self._pending_action = None
            return False
        return True

security_guard = SecurityGuard()

