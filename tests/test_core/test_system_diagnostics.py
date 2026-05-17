from __future__ import annotations

from collections import namedtuple
from types import SimpleNamespace

from aegis.core import system_diagnostics


def test_system_resource_snapshot_is_read_only(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(system_diagnostics.psutil, "virtual_memory", lambda: SimpleNamespace(
        total=16000,
        available=8000,
        used=8000,
        percent=50.0,
    ))
    monkeypatch.setattr(system_diagnostics.psutil, "disk_usage", lambda path: SimpleNamespace(
        total=1000,
        used=250,
        free=750,
        percent=25.0,
    ))
    monkeypatch.setattr(system_diagnostics.psutil, "boot_time", lambda: 100.0)
    monkeypatch.setattr(system_diagnostics.psutil, "cpu_percent", lambda interval=None: 12.5)
    monkeypatch.setattr(system_diagnostics.time, "time", lambda: 200.0)

    report = system_diagnostics.collect_system_resource_snapshot(project_root=tmp_path)

    assert report["scan_version"] == "system-resources/1"
    assert report["read_only"] is True
    assert report["status"] == "ok"
    assert report["cpu_percent"] == 12.5
    assert report["memory"]["percent"] == 50.0
    assert report["disk"]["percent"] == 25.0
    assert report["uptime_seconds"] == 100


def test_process_resource_snapshot_handles_access_denied(monkeypatch) -> None:
    class FakeProc:
        @property
        def info(self):
            raise system_diagnostics.psutil.AccessDenied(pid=10)

    monkeypatch.setattr(system_diagnostics.psutil, "process_iter", lambda attrs: [FakeProc()])

    report = system_diagnostics.collect_process_resource_snapshot()

    assert report["scan_version"] == "process-resources/1"
    assert report["read_only"] is True
    assert report["status"] == "ok"
    assert report["process_count"] == 0
    assert report["skipped"]["access_denied"] == 1
    assert report["skipped_count"] == 1


def test_process_resource_snapshot_sorts_top_memory(monkeypatch) -> None:
    class FakeProc:
        def __init__(self, pid: int, name: str, rss: int):
            self.info = {
                "pid": pid,
                "name": name,
                "memory_info": SimpleNamespace(rss=rss),
                "cpu_percent": 1.0,
            }

    monkeypatch.setattr(system_diagnostics.psutil, "process_iter", lambda attrs: [
        FakeProc(1, "small.exe", 100),
        FakeProc(2, "large.exe", 1000),
    ])

    report = system_diagnostics.collect_process_resource_snapshot(limit=1)

    assert report["top_by_memory"] == [{
        "pid": 2,
        "name": "large.exe",
        "memory_rss_bytes": 1000,
        "cpu_percent": 1.0,
    }]


def test_network_port_snapshot_reports_listeners(monkeypatch) -> None:
    Conn = namedtuple("Conn", ["laddr", "status", "pid"])

    monkeypatch.setattr(system_diagnostics.psutil, "net_connections", lambda kind: [
        Conn(("127.0.0.1", 8400), "LISTEN", 42),
        Conn(("127.0.0.1", 9999), "LISTEN", 99),
    ])
    monkeypatch.setattr(system_diagnostics, "_process_name", lambda pid: "python.exe" if pid == 42 else None)

    report = system_diagnostics.collect_network_port_snapshot(ports=(8400, 3000))

    assert report["scan_version"] == "network-ports/1"
    assert report["read_only"] is True
    assert report["status"] == "ok"
    assert report["ports"][0]["status"] == "listening"
    assert report["ports"][0]["listeners"][0]["pid"] == 42
    assert report["ports"][0]["listeners"][0]["process_name"] == "python.exe"
    assert report["ports"][1]["status"] == "free"


def test_network_port_snapshot_handles_access_denied(monkeypatch) -> None:
    def raise_access_denied(kind: str):
        raise system_diagnostics.psutil.AccessDenied(pid=None)

    monkeypatch.setattr(system_diagnostics.psutil, "net_connections", raise_access_denied)

    report = system_diagnostics.collect_network_port_snapshot(ports=(8400,))

    assert report["scan_version"] == "network-ports/1"
    assert report["read_only"] is True
    assert report["status"] == "unknown"
    assert report["error"] == "AccessDenied"
    assert report["ports"] == [{"port": 8400, "status": "unknown", "listeners": []}]
