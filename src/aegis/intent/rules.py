"""
AEGIS Intent Rules — Deterministic rule table.

Rules are evaluated in order; first match wins.
NO AI, NO guessing. If nothing matches → "unknown".

Supports Turkish and English commands.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from aegis.core.constants import RiskLevel


@dataclass(frozen=True)
class IntentRule:
    """A single deterministic intent rule."""

    intent: str
    patterns: list[str]
    risk: RiskLevel = RiskLevel.NONE
    description: str = ""


# ---------------------------------------------------------------------------
# Rule Table — evaluated top-to-bottom, first match wins
# ---------------------------------------------------------------------------

RULES: list[IntentRule] = [
    # --- App focus ---
    IntentRule(
        intent="focus_app",
        patterns=[
            r"(?P<app>not defteri|notepad|hesap makinesi|calc|premiere|adobe premiere|photoshop|adobe photoshop|explorer|cmd|powershell|chrome|spotify|browser|tarayıcı)(?:['']?e|['']?a|ye|ya)?\s+(?:odaklan|focus|öne al|one al)",
            r"(?:odaklan|focus|öne al|one al)\s+(?P<app>not defteri|notepad|hesap makinesi|calc|premiere|adobe premiere|photoshop|adobe photoshop|explorer|cmd|powershell|chrome|spotify|browser|tarayıcı)",
        ],
        risk=RiskLevel.MEDIUM,
        description="Focus an existing application window",
    ),

    # --- App closing ---
    IntentRule(
        intent="close_app",
        patterns=[
            r"(?P<app>not defteri|notepad|hesap makinesi|calc|premiere|adobe premiere|photoshop|adobe photoshop|explorer|cmd|powershell|chrome|spotify|browser|tarayıcı)\s+(?:kapat|close|quit|exit)",
            r"(?:kapat|close|quit|exit)\s+(?P<app>not defteri|notepad|hesap makinesi|calc|premiere|adobe premiere|photoshop|adobe photoshop|explorer|cmd|powershell|chrome|spotify|browser|tarayıcı)",
        ],
        risk=RiskLevel.MEDIUM,
        description="Close a running application",
    ),

    # --- Registry-backed generic focus/close ---
    IntentRule(
        intent="focus_app",
        patterns=[
            r"(?P<app>(?!https?://)[\w .&+\-]{2,80}?)(?:['’]?[ea]|\s+[ea])?\s+(?:odaklan|focus|öne al|one al)$",
            r"(?:odaklan|focus|öne al|one al)\s+(?P<app>(?!https?://)[\w .&+\-]{2,80})$",
        ],
        risk=RiskLevel.MEDIUM,
        description="Focus a registry-backed or inferred application window",
    ),
    IntentRule(
        intent="close_app",
        patterns=[
            r"(?P<app>(?!https?://)[\w .&+\-]{2,80}?)(?:['’]?[ıiuü]|\s+[ıiuü])?\s+(?:kapat|close|quit|exit)$",
            r"(?:kapat|close|quit|exit)\s+(?P<app>(?!https?://)[\w .&+\-]{2,80})$",
        ],
        risk=RiskLevel.MEDIUM,
        description="Close a registry-backed or inferred running application",
    ),

    # --- URL opening ---
    IntentRule(
        intent="open_url",
        patterns=[
            # "aç https://example.com" or "open https://..."
            r"(?:aç|open|go\s+to|navigate|git)\s+(?P<url>https?://\S+)",
            # raw URL "https://example.com"
            r"^(?P<url>https?://\S+)$",
            # Turkish order: "google aç", "youtube aç"
            r"(?P<site>google|github|youtube|stackoverflow|reddit|twitter|linkedin)\s+(?:aç|open)",
            # English order: "open google", "aç github"
            r"(?:aç|open)\s+(?P<site>google|github|youtube|stackoverflow|reddit|twitter|linkedin)",
        ],
        risk=RiskLevel.LOW,
        description="Open a URL or well-known site in browser",
    ),

    # --- App opening ---
    IntentRule(
        intent="open_app",
        patterns=[
            # Hardened patterns for Turkish order
            r"(?P<app>not defteri|notepad|hesap makinesi|calc|premiere|adobe premiere|photoshop|adobe photoshop)\s+(?:aç|open|başlat|launch)",
            # Hardened patterns for English/Verb-first order
            r"(?:aç|open|başlat|launch)\s+(?P<app>not defteri|notepad|hesap makinesi|calc|premiere|adobe premiere|photoshop|adobe photoshop|explorer|cmd|powershell|chrome|spotify|browser|tarayıcı)",
            # General patterns (already existed)
            r"(?P<app>notepad|calc|explorer|cmd|powershell|chrome|spotify|browser|tarayıcı)\s+(?:aç|open|başlat|launch)",
            # Registry-backed dynamic apps: Steam, Epic, installed games, etc.
            r"(?:aç|ac|open|başlat|launch|start)\s+(?P<app>(?!https?://)[\w .&+\-]{2,80})$",
            r"(?P<app>[\w .&+\-]{2,80})\s+(?:aç|ac|open|başlat|launch|start)$",
        ],
        risk=RiskLevel.MEDIUM,
        description="Launch a local application",
    ),

    # --- Click ---
    IntentRule(
        intent="click",
        patterns=[
            # "(500, 600) noktasına tıkla"
            r"(?P<x>\d+)[,\s]+(?P<y>\d+)\s*(?:noktasına|yerine|at)?\s*(?:tıkla|click)",
            # "tıkla (500, 600)"
            r"(?:tıkla|click)\s+(?P<x>\d+)[,\s]+(?P<y>\d+)",
            # "5 kere tıkla"
            r"(?P<count>\d+)\s*(?:kere|kez|defa|sefer)\s+(?:tıkla|click)",
            r"(?:tıkla|click)\s+(?P<count>\d+)\s*(?:kere|kez|defa|sefer|times?)",
            r"click\s+(?P<count>\d+)\s*times?",
            # just "tıkla"
            r"^(?:tıkla|click)$",
        ],
        risk=RiskLevel.MEDIUM,
        description="Click at screen coordinates",
    ),

    # --- Write File ---
    IntentRule(
        intent="write_file",
        patterns=[
            r"(?P<path>\S+\.\w+)\s+(?:dosyasına|yerine)\s+(?P<content>.+?)\s*(?:yaz|save|write)",
            r"(?:yaz|save|write)\s+(?P<content>.+?)\s+(?:dosyasına|yoluna|path|to)\s+(?P<path>\S+)",
        ],
        risk=RiskLevel.MEDIUM,
        description="Write content to a local file",
    ),

    # --- Type/Keyboard input ---
    IntentRule(
        intent="type",
        patterns=[
            # "notepad'e merhaba dünya yaz"
            r"(?P<window>.+?)(?:[''e|''a|''ye|''ya|e|a|ye|ya])\s+(?P<text>.+?)\s+(?:yaz|type|yazdır)$",
            # "yaz merhaba dünya"
            r"^(?:yaz|type|write)\s+(?P<text>.+)",
            # "merhaba dünya yaz"
            r"^(?P<text>.+?)\s+(?:yaz|type|yazdır)$",
        ],
        risk=RiskLevel.MEDIUM,
        description="Type text into current focused element or specific window",
    ),

    # --- File reading ---
    IntentRule(
        intent="read_file",
        patterns=[
            r"(?:oku|read|göster|show|cat)\s+(?P<path>\S+\.\w+)",
            r"(?:dosya|file)\s+(?:oku|read)\s+(?P<path>\S+)",
        ],
        risk=RiskLevel.LOW,
        description="Read a local file",
    ),

    # --- Safe file inspection ---
    IntentRule(
        intent="list_directory",
        patterns=[
            r"^(?:list|ls|dir|listele)(?:\s+(?P<path>\S+))?$",
            r"^(?:klas[öo]r|directory)\s+(?:listele|list)(?:\s+(?P<path>\S+))?$",
        ],
        risk=RiskLevel.LOW,
        description="List a directory without mutating files",
    ),
    IntentRule(
        intent="search_files",
        patterns=[
            r"^(?:search files|find files|dosya ara)\s+(?P<query>.+?)(?:\s+(?:in|i[çc]inde)\s+(?P<path>\S+))?$",
        ],
        risk=RiskLevel.LOW,
        description="Search file names without mutating files",
    ),
    IntentRule(
        intent="grep_in_files",
        patterns=[
            r"^(?:grep|search in files|i[çc]erikte ara)\s+(?P<query>.+?)(?:\s+(?:in|i[çc]inde)\s+(?P<path>\S+))?$",
        ],
        risk=RiskLevel.LOW,
        description="Search file contents without mutating files",
    ),
    IntentRule(
        intent="file_info",
        patterns=[
            r"^(?:file info|stat|dosya bilgisi)\s+(?P<path>\S+)$",
        ],
        risk=RiskLevel.LOW,
        description="Read file metadata",
    ),

    # --- File create/edit preview-capable tools ---
    IntentRule(
        intent="create_file",
        patterns=[
            r"^(?:create file|dosya oluştur|dosya olustur)\s+(?P<path>\S+)(?:\s+(?:with|i[çc]erik)\s+(?P<content>.+))?$",
        ],
        risk=RiskLevel.MEDIUM,
        description="Create a file inside the workspace boundary",
    ),
    IntentRule(
        intent="edit_file",
        patterns=[
            r"^(?:edit file|dosya d[üu]zenle)\s+(?P<path>\S+)\s+(?:replace|de[ğg]iştir|degistir)\s+(?P<target>.+?)\s+(?:with|ile)\s+(?P<replacement>.+)$",
        ],
        risk=RiskLevel.MEDIUM,
        description="Edit a file inside the workspace boundary",
    ),
    IntentRule(
        intent="delete_file",
        patterns=[
            r"^(?:delete file|delete|sil)\s+(?P<path>\S+)$",
        ],
        risk=RiskLevel.CRITICAL,
        description="Blocked critical file deletion",
    ),
    IntentRule(
        intent="move_file",
        patterns=[
            r"^(?:move file|move|taşı|tasi)\s+(?P<path>\S+)\s+(?:to|->|hedefine)\s+(?P<destination>\S+)$",
        ],
        risk=RiskLevel.CRITICAL,
        description="Blocked critical file move",
    ),

    # --- Web search ---
    IntentRule(
        intent="search_web",
        patterns=[
            r"(?P<query>.+)\s+(?:araması|arama)\s+yap\b",
            r"(?:ara|search|bul|find|google['']?la)\b\s+(?P<query>.+)",
            r"(?P<query>.+)\s+(?:ara|search|bul|buluver|google['']?la)\b",
            r"(?:web|internet)\s*(?:de|da|te|ta)?\s*(?:ara|search)\b\s+(?P<query>.+)",
        ],
        risk=RiskLevel.LOW,
        description="Search the web for information",
    ),

    # --- Summarize ---
    IntentRule(
        intent="summarize_file",
        patterns=[
            r"(?:özetle|summarize|özet)\s+(?P<path>\S+)",
        ],
        risk=RiskLevel.LOW,
        description="Summarize a file's contents",
    ),

    # --- Scroll ---
    IntentRule(
        intent="scroll",
        patterns=[
            r"(?:aşağı|yukarı|down|up)?\s*(?:kaydır|scroll)\b",
            r"(?:sayfayı|page)\s+(?:indir|kaldır|kaydır|scroll)",
        ],
        risk=RiskLevel.LOW,
        description="Scroll the current web page",
    ),

    # --- Wait ---
    IntentRule(
        intent="wait",
        patterns=[
            r"(?P<seconds>\d+(?:\.\d+)?)\s*(?:saniye|sn|seconds?|secs?)\s*(?:bekle|wait)",
            r"(?:bekle|wait)\s*(?P<seconds>\d+(?:\.\d+)?)\s*(?:saniye|sn|seconds?|secs?)",
        ],
        risk=RiskLevel.LOW,
        description="Wait for a specific duration",
    ),

    # --- Git Operations ---
    IntentRule(
        intent="git_action",
        patterns=[
            r"^(?:git|github)\s+(?P<git_cmd>push|pull|fetch|commit|status|add|pushla|çek|güncelle)\b",
            r"^(?P<git_cmd>pushla|commit'le|commit-le)\b",
        ],
        risk=RiskLevel.MEDIUM,
        description="Execute git commands",
    ),

    # --- Shell introspection ---
    IntentRule(
        intent="run_command",
        patterns=[
            r"^(?:run command|shell|komut çalıştır|komut calistir)\s+(?P<command>.+)$",
        ],
        risk=RiskLevel.LOW,
        description="Run allowlisted read-only shell introspection",
    ),

    # --- General chat ---
    IntentRule(
        intent="general_chat",
        patterns=[
            r"^(?:merhaba|hello|hi|hey|selam|naber|nasılsın)\b",
            r"^(?:ne yapabilirsin|what can you do|help|yardım)\b",
        ],
        risk=RiskLevel.NONE,
        description="General conversation or help request",
    ),
]

# Well-known site name → URL mapping
KNOWN_SITES: dict[str, str] = {
    "google": "https://www.google.com",
    "github": "https://github.com",
    "youtube": "https://www.youtube.com",
    "stackoverflow": "https://stackoverflow.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://twitter.com",
    "linkedin": "https://www.linkedin.com",
}

# Application name aliases for normalization (Flat mapping for speed and accuracy)
APP_ALIASES: dict[str, str] = {
    "not defteri": "notepad",
    "notepad": "notepad",
    "hesap makinesi": "calc",
    "calculator": "calc",
    "calc": "calc",
    "chrome": "chrome",
    "google chrome": "chrome",
    "brave": "brave",
    "brave browser": "brave",
    "brave tarayıcı": "brave",
    "browser": "chrome",
    "tarayıcı": "chrome",
    "spotify": "spotify",
    "explorer": "explorer",
    "dosya gezgini": "explorer",
    "cmd": "cmd",
    "komut istemi": "cmd",
    "terminal": "cmd",
    "powershell": "powershell",
    "photoshop": "photoshop",
    "adobe photoshop": "photoshop",
    "premiere": "premiere",
    "adobe premiere": "premiere",
    "premiere pro": "premiere",
    "antigravity": "antigravity",
    "antigravity ide": "antigravity",
    "antigravity i": "antigravity",
    "google antigravity": "antigravity",
    "antigravity agent manager": "antigravity_agent_manager",
    "antigravity manager": "antigravity_agent_manager",
}
# Verification Metadata for Tier 4 Deterministic Tracking
# Maps canonical app ID -> {process_name, keywords}
VERIFICATION_METADATA: dict[str, dict[str, Any]] = {
    "notepad": {"process_name": "notepad.exe", "keywords": ["Notepad", "Not Defteri"]},
    "calc": {"process_name": "CalculatorApp.exe", "keywords": ["Calculator", "Hesap Makinesi"]},
    "chrome": {"process_name": "chrome.exe", "keywords": ["Google Chrome"]},
    "brave": {"process_name": "brave.exe", "keywords": ["Brave", "New Tab"]},
    "cmd": {"process_name": "cmd.exe", "keywords": ["Command Prompt", "Komut İstemi"]},
    "powershell": {"process_name": "powershell.exe", "keywords": ["PowerShell"]},
    "spotify": {"process_name": "Spotify.exe", "keywords": ["Spotify"]},
    "explorer": {"process_name": "explorer.exe", "keywords": ["File Explorer", "Dosya Gezgini"]},
    "antigravity": {"process_name": "Antigravity IDE.exe", "keywords": ["Antigravity", "Antigravity IDE"]},
    "antigravity_agent_manager": {
        "process_name": "Antigravity.exe",
        "keywords": ["Antigravity Agent Manager", "Antigravity"],
    },
}
