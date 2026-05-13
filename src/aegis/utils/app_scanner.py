import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class AppScanner:
    """Scans Windows directories to build a map of installed applications."""
    
    def __init__(self):
        self.common_paths = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            os.path.join(os.environ.get("AppData", ""), "..", "Local").replace("..", ""), # Local AppData
        ]
        self._cache: Dict[str, str] = {}

    def scan(self) -> Dict[str, str]:
        """Performs a shallow scan of program directories for .exe files."""
        logger.info("[SCANNER] Starting application scan...")
        apps = {}
        
        for base_path in self.common_paths:
            if not os.path.exists(base_path):
                continue
                
            try:
                # We do a shallow scan (top 2 levels) to keep it fast
                # Deep scanning can be very slow
                for entry in os.scandir(base_path):
                    if entry.is_dir():
                        try:
                            for sub_entry in os.scandir(entry.path):
                                if sub_entry.is_file() and sub_entry.name.lower().endswith(".exe"):
                                    name = sub_entry.name.lower().replace(".exe", "")
                                    if name not in apps: # Don't overwrite
                                        apps[name] = sub_entry.path
                        except:
                            continue
            except Exception as e:
                logger.warning(f"[SCANNER] Failed to scan {base_path}: {e}")
                
        self._cache = apps
        logger.info(f"[SCANNER] Found {len(apps)} applications.")
        return apps

_scanner = AppScanner()

def get_app_scanner() -> AppScanner:
    return _scanner
