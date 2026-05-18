# src/aegis/replay/golden_journal.py

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Any
from aegis.core.schemas import ActionResult

logger = logging.getLogger(__name__)

class GoldenJournal:
    """
    AEGIS Golden Replay System.
    Records high-fidelity traces for regression testing and reliability analysis.
    """
    def __init__(self, storage_dir: str = "./data/golden_traces"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def record(self, trace_id: str, goal: str, actions: List[ActionResult], metrics: dict):
        """Save a complete execution trace to disk."""
        trace_file = self.storage_dir / f"{trace_id}.json"
        
        data = {
            "metadata": {
                "trace_id": trace_id,
                "goal": goal,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "final_status": metrics.get("status"),
                "avg_determinism": metrics.get("avg_determinism"),
                "recovery_used": metrics.get("recovery_used")
            },
            "timeline": [action.model_dump(mode="json") for action in actions]
        }
        
        try:
            with open(trace_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"[JOURNAL] Golden Trace secured: {trace_file}")
        except Exception as e:
            logger.error(f"[JOURNAL] Failed to secure trace: {e}")

def get_journal() -> GoldenJournal:
    return GoldenJournal()
