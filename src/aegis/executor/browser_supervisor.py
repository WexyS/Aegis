import asyncio
import logging
import time
import weakref
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BrowserMetrics:
    active_contexts: int
    active_pages: int
    leaked_handles: int
    cleanup_count: int
    avg_context_lifetime: float
    total_contexts_created: int

class BrowserSupervisor:
    """
    Playwright Resource Watchdog.
    Tracks, prunes, and supervises browser contexts to prevent memory leaks in long-running sessions.
    """
    def __init__(self):
        self._contexts = weakref.WeakSet()
        self._pages = weakref.WeakSet()
        
        # Track creation times for lifetime metrics
        self._context_lifetimes: Dict[int, float] = {}  # id(context) -> start_time
        self._historical_lifetimes: List[float] = []
        
        self.cleanup_count = 0
        self.total_contexts_created = 0
        self.max_lifetime_sec = 3600  # 1 hour max lifetime
        self.idle_timeout_sec = 600   # 10 mins idle
        
        self._watchdog_task: Optional[asyncio.Task] = None
        self._is_running = False

    def start(self):
        """Start the background watchdog."""
        if self._watchdog_task is None or self._watchdog_task.done():
            self._is_running = True
            self._watchdog_task = asyncio.create_task(self._supervise_loop())
            logger.info("[WATCHDOG] Browser Resource Supervisor started.")

    async def stop(self):
        """Stop the watchdog and force cleanup."""
        self._is_running = False
        if self._watchdog_task:
            self._watchdog_task.cancel()
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass
        await self.force_cleanup()

    def register_context(self, context):
        """Register a new Playwright context for tracking."""
        self._contexts.add(context)
        self._context_lifetimes[id(context)] = time.time()
        self.total_contexts_created += 1
        
        # Patch the close method to record lifetime
        original_close = context.close
        async def tracked_close(*args, **kwargs):
            self._record_lifetime(context)
            try:
                await original_close(*args, **kwargs)
            except Exception as e:
                logger.warning(f"[WATCHDOG] Error closing context: {e}")
        context.close = tracked_close

    def register_page(self, page):
        """Register a new Playwright page for tracking."""
        self._pages.add(page)

    def _record_lifetime(self, context):
        cid = id(context)
        start_time = self._context_lifetimes.pop(cid, None)
        if start_time:
            self._historical_lifetimes.append(time.time() - start_time)
            # Keep only last 100 for avg
            if len(self._historical_lifetimes) > 100:
                self._historical_lifetimes.pop(0)

    async def _supervise_loop(self):
        """Background loop to prune stale resources."""
        while self._is_running:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.prune_stale_resources()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[WATCHDOG] Supervisor loop error: {e}")

    async def prune_stale_resources(self):
        """Check all contexts for max lifetime violations and prune them."""
        now = time.time()
        stale_contexts = []
        
        for context in list(self._contexts):
            start_time = self._context_lifetimes.get(id(context))
            if start_time and (now - start_time) > self.max_lifetime_sec:
                stale_contexts.append(context)
                
        for ctx in stale_contexts:
            logger.warning(f"[WATCHDOG] Force-closing stale browser context (Lifetime > {self.max_lifetime_sec}s).")
            try:
                await ctx.close()
                self.cleanup_count += 1
            except Exception as e:
                logger.error(f"[WATCHDOG] Failed to close stale context: {e}")

    async def force_cleanup(self):
        """Emergency cleanup: Force close ALL tracked pages and contexts."""
        logger.warning("[WATCHDOG] Executing emergency force-cleanup of all tracked browser resources.")
        for page in list(self._pages):
            try:
                if not page.is_closed():
                    await page.close()
            except Exception:
                pass
                
        for context in list(self._contexts):
            try:
                await context.close()
                self.cleanup_count += 1
            except Exception:
                pass
                
        self._contexts.clear()
        self._pages.clear()
        self._context_lifetimes.clear()

    def get_metrics(self) -> BrowserMetrics:
        """Return watchdog telemetry."""
        avg_lifetime = 0.0
        if self._historical_lifetimes:
            avg_lifetime = sum(self._historical_lifetimes) / len(self._historical_lifetimes)
            
        # Count orphaned keys in _context_lifetimes as leaked handles
        active_ids = {id(c) for c in self._contexts}
        leaked_handles = len([cid for cid in self._context_lifetimes.keys() if cid not in active_ids])
        
        return BrowserMetrics(
            active_contexts=len(self._contexts),
            active_pages=len(self._pages),
            leaked_handles=leaked_handles,
            cleanup_count=self.cleanup_count,
            avg_context_lifetime=avg_lifetime,
            total_contexts_created=self.total_contexts_created
        )

# Global singleton instance
_supervisor_instance = None

def get_browser_supervisor() -> BrowserSupervisor:
    global _supervisor_instance
    if _supervisor_instance is None:
        _supervisor_instance = BrowserSupervisor()
    return _supervisor_instance
