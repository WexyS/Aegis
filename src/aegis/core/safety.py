import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

class SafetyGuard:
    """
    AEGIS Safety Guard — Central security filter for all agent actions.
    Protects the OS from destructive commands and sensitive path access.
    """

    FORBIDDEN_KEYWORDS = [
        r"\bdel\b", r"\bformat\b", r"\brmdir\b", r"\berase\b",
        r"\bshutdown\b", r"\breboot\b", r"\breg\s+delete\b"
    ]
    
    FORBIDDEN_PATHS = [
        r"C:\\Windows", r"C:\\Program Files", r"C:\\System32",
        r"\\etc\\", r"\\root\\"
    ]

    def is_safe(self, tool_name: str, params: dict[str, Any]) -> tuple[bool, str]:
        """Check if an action is safe to execute."""
        param_str = str(params).lower()

        # 1. Check for forbidden destructive keywords
        for pattern in self.FORBIDDEN_KEYWORDS:
            if re.search(pattern, param_str, re.IGNORECASE):
                return False, f"Potentially destructive command detected: '{pattern}'"

        # 2. Check for sensitive path access
        for path in self.FORBIDDEN_PATHS:
            if path.lower() in param_str:
                return False, f"Access to sensitive system path is blocked: '{path}'"

        # 3. Specific Tool Hardening
        if tool_name == "open_app":
            app = params.get("app", "").lower()
            if app in ["regedit", "control panel", "cmd", "powershell"]:
                # We might want to allow cmd/powershell later, but for now block for safety
                return False, f"Launching system management tool '{app}' is restricted."

        return True, "Safe"

_guard = SafetyGuard()

def get_safety_guard() -> SafetyGuard:
    return _guard
