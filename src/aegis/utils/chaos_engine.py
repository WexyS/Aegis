# src/aegis/utils/chaos_engine.py

import random
import asyncio
import logging
import pygetwindow as gw
import pyautogui

logger = logging.getLogger(__name__)

class ChaosEngine:
    """
    AEGIS Chaos Testing Suite (Reliability Science).
    Deliberately injects system-level noise to test agent resilience and recovery.
    """
    
    @staticmethod
    async def steal_focus():
        """Randomly activate a different window to test focus recovery."""
        windows = [w for w in gw.getAllWindows() if w.title and w.visible]
        if windows:
            target = random.choice(windows)
            try:
                target.activate()
                logger.warning(f"[CHAOS] Focus stolen to: {target.title}")
            except Exception:
                pass

    @staticmethod
    async def jitter_cursor():
        """Random cursor movement to test coordinate-based reliability."""
        x, y = pyautogui.position()
        pyautogui.moveTo(x + random.randint(-100, 100), y + random.randint(-100, 100))
        logger.warning("[CHAOS] Cursor jitter injected.")

    @staticmethod
    async def minimize_active():
        """Minimize the active window to test visibility recovery."""
        active = gw.getActiveWindow()
        if active:
            try:
                active.minimize()
                logger.warning(f"[CHAOS] Active window minimized: {active.title}")
            except Exception:
                pass

    @staticmethod
    async def inject_noise(probability: float = 0.2):
        """Randomly decide to inject noise based on probability."""
        if random.random() < probability:
            effect = random.choice([
                ChaosEngine.steal_focus,
                ChaosEngine.jitter_cursor,
                ChaosEngine.minimize_active
            ])
            await effect()
