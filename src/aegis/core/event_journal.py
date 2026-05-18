from __future__ import annotations

import json
import logging
import os
import errno
import threading
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, Iterator

from aegis.core.config import get_settings
from aegis.core.protocol import GENESIS_HASH, RuntimeEvent, ensure_sequence_at_least, finalize_event


logger = logging.getLogger(__name__)
_process_file_lock = threading.RLock()


class RuntimeEventJournal:
    """Append-only canonical runtime event journal."""

    def __init__(self, max_memory_events: int = 10000) -> None:
        settings = get_settings()
        self.log_dir = Path(settings.logging.directory)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.log_dir / "runtime_events.jsonl"
        self.lock_path = self.log_dir / "runtime_events.lock"
        self._lock = threading.Lock()
        self._events: Deque[dict] = deque(maxlen=max_memory_events)
        self._max_memory_events = max_memory_events
        self._seen_ids: set[str] = set()
        self._last_hash = GENESIS_HASH
        self._disk_size = 0
        self._load_existing_tail()

    def append(self, event: RuntimeEvent) -> RuntimeEvent:
        """Finalize, persist, and keep a bounded in-memory copy of an event."""
        with self._lock:
            with self._journal_file_lock():
                self._sync_from_disk_locked()
                if event.event_id in self._seen_ids:
                    return event

                finalize_event(event, self._last_hash)
                data = event.to_dict()

                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
                    f.flush()
                    os.fsync(f.fileno())

                self._events.append(data)
                self._seen_ids.add(event.event_id)
                self._last_hash = event.event_hash or self._last_hash
                self._disk_size = self.path.stat().st_size if self.path.exists() else self._disk_size
                return event

    def events_after(self, sequence_num: int) -> list[dict]:
        with self._lock:
            with self._journal_file_lock():
                self._sync_from_disk_locked()
                if self._events:
                    try:
                        earliest_memory_sequence = int(self._events[0].get("sequence_num", -1))
                    except (TypeError, ValueError):
                        earliest_memory_sequence = -1
                    if int(sequence_num) >= earliest_memory_sequence:
                        return [e for e in self._events if int(e.get("sequence_num", -1)) > sequence_num]
                return [e for e in self._iter_disk_events_locked() if int(e.get("sequence_num", -1)) > sequence_num]

    def recent_events(self, limit: int | None = None) -> list[dict]:
        with self._lock:
            events = list(self._events)
            if limit is None:
                return events
            bounded_limit = max(int(limit), 0)
            if bounded_limit == 0:
                return []
            return events[-bounded_limit:]

    def snapshot(self) -> dict:
        with self._lock:
            last_event = self._events[-1] if self._events else None
            integrity = self.verify_integrity_locked()
            return {
                "event_count": len(self._events),
                "last_sequence_num": last_event.get("sequence_num", 0) if last_event else 0,
                "last_event_hash": self._last_hash,
                "journal_path": str(self.path),
                "integrity_status": integrity["status"],
                "integrity_checked_events": integrity["checked_events"],
                "integrity_chain_resets": integrity.get("chain_resets", 0),
                "integrity_error": integrity.get("error"),
                "active_chain_start_sequence": integrity.get("active_chain_start_sequence"),
                "historical_integrity_status": integrity.get("historical_status"),
                "historical_integrity_error": integrity.get("historical_error"),
                "historical_integrity_breaks": integrity.get("historical_breaks", 0),
            }

    def verify_integrity_locked(self) -> dict:
        previous = None
        checked = 0
        chain_resets = 0
        active_chain_start_sequence = None
        active_chain_start_index = 0
        historical_error = None
        historical_breaks = 0
        for index, event in enumerate(self._events):
            if previous is not None and event.get("previous_hash") != previous.get("event_hash"):
                session_changed = event.get("session_id") != previous.get("session_id")
                if event.get("previous_hash") == GENESIS_HASH and session_changed:
                    chain_resets += 1
                    previous = event
                    checked += 1
                    continue
                historical_breaks += 1
                if historical_error is None:
                    historical_error = f"Hash link mismatch at sequence {event.get('sequence_num')}"
                active_chain_start_sequence = event.get("sequence_num")
                active_chain_start_index = index
            previous = event
            if active_chain_start_sequence is None:
                active_chain_start_sequence = event.get("sequence_num")
            checked += 1
        return {
            "status": "hash-chain",
            "checked_events": checked,
            "chain_resets": chain_resets,
            "active_chain_start_sequence": active_chain_start_sequence,
            "active_chain_start_index": active_chain_start_index,
            "historical_status": "broken" if historical_breaks else "hash-chain",
            "historical_error": historical_error,
            "historical_breaks": historical_breaks,
        }

    def repair_historical_breaks(self) -> dict:
        """Archive mixed/corrupt history and keep the latest valid active suffix."""
        with self._lock:
            with self._journal_file_lock():
                self._reload_from_disk_locked()
                integrity = self.verify_integrity_locked()
                if integrity.get("historical_breaks", 0) == 0:
                    return {
                        "repaired": False,
                        "reason": "journal already clean",
                        "event_count": len(self._events),
                        "integrity_status": integrity["status"],
                        "historical_integrity_status": integrity["historical_status"],
                    }

                events = list(self._events)
                start_index = int(integrity.get("active_chain_start_index", 0) or 0)
                active_events = events[start_index:] if events else []
                archive_dir = self.log_dir / "archive"
                archive_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                archive_path = archive_dir / f"runtime_events_{timestamp}_historical_broken.jsonl"
                temp_path = self.path.with_name("runtime_events.jsonl.repairing")
                if temp_path.exists():
                    temp_path.unlink()

                with temp_path.open("w", encoding="utf-8") as f:
                    for event in active_events:
                        f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")

                self.path.replace(archive_path)
                temp_path.replace(self.path)
                self._reload_from_disk_locked()
                repaired_integrity = self.verify_integrity_locked()
                return {
                    "repaired": True,
                    "archived_path": str(archive_path),
                    "archived_event_count": len(events),
                    "active_event_count": len(self._events),
                    "active_chain_start_sequence": integrity.get("active_chain_start_sequence"),
                    "integrity_status": repaired_integrity["status"],
                    "historical_integrity_status": repaired_integrity["historical_status"],
                    "historical_integrity_breaks": repaired_integrity["historical_breaks"],
                }

    @contextmanager
    def _journal_file_lock(self) -> Iterator[None]:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with _process_file_lock:
            with self.lock_path.open("a+b") as lock_file:
                if os.name == "nt":
                    import msvcrt

                    lock_file.seek(0)
                    locked = False
                    try:
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
                        locked = True
                    except OSError as exc:
                        if exc.errno != errno.EDEADLK:
                            raise
                    try:
                        yield
                    finally:
                        if locked:
                            lock_file.seek(0)
                            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                    try:
                        yield
                    finally:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _load_existing_tail(self) -> None:
        with self._journal_file_lock():
            self._reload_from_disk_locked()

    def _reload_from_disk_locked(self) -> None:
        self._events = deque(maxlen=self._max_memory_events)
        self._seen_ids.clear()
        self._last_hash = GENESIS_HASH
        self._disk_size = 0

        if not self.path.exists():
            return

        try:
            max_sequence = 0
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    self._events.append(event)
                    max_sequence = max(max_sequence, int(event.get("sequence_num", 0) or 0))
                    if event_id := event.get("event_id"):
                        self._seen_ids.add(event_id)
                    if event_hash := event.get("event_hash"):
                        self._last_hash = event_hash
            self._disk_size = self.path.stat().st_size
            ensure_sequence_at_least(max_sequence)
        except Exception:
            logger.exception("Failed to reload runtime event journal from disk: %s", self.path)
            self._events.clear()
            self._seen_ids.clear()
            self._last_hash = GENESIS_HASH
            self._disk_size = 0

    def _sync_from_disk_locked(self) -> None:
        """Incrementally absorb events appended by other journal instances."""
        if not self.path.exists():
            self._disk_size = 0
            return

        current_size = self.path.stat().st_size
        if current_size < self._disk_size:
            self._reload_from_disk_locked()
            return
        if current_size == self._disk_size:
            return

        try:
            max_sequence = 0
            with self.path.open("r", encoding="utf-8") as f:
                f.seek(self._disk_size)
                for line in f:
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    self._events.append(event)
                    max_sequence = max(max_sequence, int(event.get("sequence_num", 0) or 0))
                    if event_id := event.get("event_id"):
                        self._seen_ids.add(event_id)
                    if event_hash := event.get("event_hash"):
                        self._last_hash = event_hash
            self._disk_size = current_size
            ensure_sequence_at_least(max_sequence)
        except Exception:
            logger.exception("Failed to incrementally sync runtime event journal from disk: %s", self.path)
            self._reload_from_disk_locked()

    def _iter_disk_events_locked(self) -> Iterator[dict]:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    yield json.loads(line)
        except Exception:
            logger.exception("Failed to read runtime event journal from disk: %s", self.path)
            return


_instance: RuntimeEventJournal | None = None
_lock = threading.Lock()


def get_runtime_journal() -> RuntimeEventJournal:
    global _instance
    with _lock:
        if _instance is None:
            _instance = RuntimeEventJournal()
        return _instance
