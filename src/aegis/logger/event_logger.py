# src/aegis/logger/event_logger.py

import json
import logging
import os
import threading
import queue
import time
from datetime import datetime, timezone
from aegis.core.constants import EventType
from typing import Any, Dict, Optional
from uuid import UUID


class EventLogger:
    """
    AEGIS Elite Event Logger.
    Optimized for high-throughput with persistent file handles and backpressure management.
    """
    def __init__(self, log_dir: str = "logs", max_queue_size: int = 10000):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"aegis_trace_{timestamp}.jsonl")
        
        # Optimized IO: Keep handle open
        self._file_handle = open(self.log_file, "a", encoding="utf-8", buffering=1) # Line buffered
        
        # Backpressure: Bound the queue to prevent RAM exhaustion
        self.queue = queue.Queue(maxsize=max_queue_size)
        self.stop_event = threading.Event()
        self._console_logger = logging.getLogger("aegis")
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def _worker(self):
        """Persistent background worker for efficient disk I/O."""
        while not self.stop_event.is_set() or not self.queue.empty():
            try:
                # Batch processing could be added here for even higher throughput
                entry = self.queue.get(timeout=0.1)
                self._file_handle.write(json.dumps(entry) + "\n")
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self._console_logger.critical("Logger worker failure: %s", e)

    def log(self, 
            event_type: EventType, 
            data: Dict[str, Any], 
            trace_id: UUID, 
            span_id: UUID, 
            parent_span_id: Optional[UUID] = None,
            level: str = "INFO"):
        """
        Submits a log entry with Priority-Aware backpressure.
        High-priority events (ERROR, SYSTEM_ERROR, VERIFICATION_FAILED) are never dropped.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "unix_time": time.time(),
            "trace_id": str(trace_id),
            "span_id": str(span_id),
            "parent_span_id": str(parent_span_id) if parent_span_id else None,
            "event_type": event_type.value,
            "level": level,
            "data": data
        }
        
        # Priority Check: Critical failure data must be preserved for Replay/Debug
        is_critical = level == "ERROR" or event_type in [
            EventType.SYSTEM_ERROR, 
            EventType.VERIFICATION_FAILED, 
            EventType.ACTION_FAILED
        ]

        try:
            if is_critical:
                # Block for critical events to ensure integrity
                self.queue.put(entry, block=True, timeout=1.0)
            else:
                # Drop strategy for non-critical telemetry to protect main loop
                self.queue.put_nowait(entry)
        except queue.Full:
            if is_critical:
                # Last resort: Force direct write to prevent data loss on critical fail
                try:
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(entry) + "\n")
                except Exception as exc:
                    self._console_logger.critical("Direct critical log write failed: %s", exc)
        
        # Console mirror
        msg = f"[{event_type.value}] {data.get('message', data)}"
        if level == "ERROR":
            self._console_logger.error(msg)
        elif level == "WARNING":
            self._console_logger.warning(msg)
        else:
            self._console_logger.info(msg)

    def shutdown(self):
        """Ensures all logs are flushed and file handles are closed safely."""
        self.stop_event.set()
        self.worker_thread.join(timeout=2.0)
        if self._file_handle:
            self._file_handle.flush()
            self._file_handle.close()

_instance = None
_lock = threading.Lock()

def get_event_logger() -> EventLogger:
    global _instance
    with _lock:
        if _instance is None:
            _instance = EventLogger()
    return _instance
