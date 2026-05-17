from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Iterable

import psutil

from aegis.core.config import PROJECT_ROOT


DEFAULT_DEV_PORTS = (8400, 3000)


def collect_system_resource_snapshot(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Read-only CPU, memory, disk, and uptime snapshot."""
    started_at = int(time.time() * 1000)
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(_disk_target(project_root))
        boot_time = psutil.boot_time()
        cpu_percent = psutil.cpu_percent(interval=None)
    except Exception as exc:
        return {
            "scan_version": "system-resources/1",
            "read_only": True,
            "status": "unknown",
            "error": type(exc).__name__,
            "started_at": started_at,
            "completed_at": int(time.time() * 1000),
        }

    return {
        "scan_version": "system-resources/1",
        "read_only": True,
        "status": "warning" if max(float(cpu_percent), float(memory.percent), float(disk.percent)) >= 90.0 else "ok",
        "cpu_percent": float(cpu_percent),
        "memory": {
            "total_bytes": int(memory.total),
            "available_bytes": int(memory.available),
            "used_bytes": int(memory.used),
            "percent": float(memory.percent),
        },
        "disk": {
            "path": _disk_target(project_root),
            "total_bytes": int(disk.total),
            "used_bytes": int(disk.used),
            "free_bytes": int(disk.free),
            "percent": float(disk.percent),
        },
        "uptime_seconds": max(0, int(time.time() - boot_time)),
        "started_at": started_at,
        "completed_at": int(time.time() * 1000),
    }


def collect_process_resource_snapshot(limit: int = 5) -> dict[str, Any]:
    """Read-only process resource snapshot sorted by resident memory."""
    started_at = int(time.time() * 1000)
    processes: list[dict[str, Any]] = []
    skipped = {"access_denied": 0, "no_such_process": 0, "other": 0}

    try:
        iterator = psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"])
        for proc in iterator:
            try:
                info = dict(proc.info)
                memory_info = info.get("memory_info")
                rss_bytes = int(getattr(memory_info, "rss", 0) or 0)
                processes.append({
                    "pid": int(info.get("pid") or 0),
                    "name": str(info.get("name") or "unknown"),
                    "memory_rss_bytes": rss_bytes,
                    "cpu_percent": _safe_float(info.get("cpu_percent")),
                })
            except psutil.AccessDenied:
                skipped["access_denied"] += 1
            except psutil.NoSuchProcess:
                skipped["no_such_process"] += 1
            except Exception:
                skipped["other"] += 1
    except psutil.AccessDenied:
        return _process_snapshot_error("AccessDenied", started_at, skipped)
    except Exception as exc:
        return _process_snapshot_error(type(exc).__name__, started_at, skipped)

    top_by_memory = sorted(processes, key=lambda item: item["memory_rss_bytes"], reverse=True)[:limit]
    return {
        "scan_version": "process-resources/1",
        "read_only": True,
        "status": "ok",
        "process_count": len(processes),
        "top_by_memory": top_by_memory,
        "skipped": skipped,
        "skipped_count": sum(skipped.values()),
        "started_at": started_at,
        "completed_at": int(time.time() * 1000),
    }


def collect_network_port_snapshot(ports: Iterable[int] = DEFAULT_DEV_PORTS) -> dict[str, Any]:
    """Read-only listener snapshot for development ports."""
    started_at = int(time.time() * 1000)
    target_ports = [int(port) for port in ports]
    try:
        connections = psutil.net_connections(kind="inet")
    except psutil.AccessDenied:
        return _network_snapshot_error("AccessDenied", started_at, target_ports)
    except Exception as exc:
        return _network_snapshot_error(type(exc).__name__, started_at, target_ports)

    listeners_by_port: dict[int, list[dict[str, Any]]] = {port: [] for port in target_ports}
    for conn in connections:
        local_port = _local_port(conn)
        if local_port not in listeners_by_port or str(getattr(conn, "status", "")).upper() != "LISTEN":
            continue
        pid = getattr(conn, "pid", None)
        listeners_by_port[local_port].append({
            "pid": pid,
            "process_name": _process_name(pid),
            "address": _local_address(conn),
            "status": str(getattr(conn, "status", "")),
        })

    port_entries = [
        {
            "port": port,
            "status": "listening" if listeners_by_port[port] else "free",
            "listeners": listeners_by_port[port],
        }
        for port in target_ports
    ]
    return {
        "scan_version": "network-ports/1",
        "read_only": True,
        "status": "ok",
        "ports": port_entries,
        "started_at": started_at,
        "completed_at": int(time.time() * 1000),
    }


def _disk_target(project_root: Path) -> str:
    root = Path(project_root)
    return str(root.anchor or root)


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _process_snapshot_error(error: str, started_at: int, skipped: dict[str, int]) -> dict[str, Any]:
    return {
        "scan_version": "process-resources/1",
        "read_only": True,
        "status": "unknown",
        "error": error,
        "process_count": 0,
        "top_by_memory": [],
        "skipped": skipped,
        "skipped_count": sum(skipped.values()),
        "started_at": started_at,
        "completed_at": int(time.time() * 1000),
    }


def _network_snapshot_error(error: str, started_at: int, ports: list[int]) -> dict[str, Any]:
    return {
        "scan_version": "network-ports/1",
        "read_only": True,
        "status": "unknown",
        "error": error,
        "ports": [{"port": port, "status": "unknown", "listeners": []} for port in ports],
        "started_at": started_at,
        "completed_at": int(time.time() * 1000),
    }


def _local_port(conn: Any) -> int | None:
    laddr = getattr(conn, "laddr", None)
    port = getattr(laddr, "port", None)
    if port is not None:
        return int(port)
    if isinstance(laddr, tuple) and len(laddr) >= 2:
        return int(laddr[1])
    return None


def _local_address(conn: Any) -> str | None:
    laddr = getattr(conn, "laddr", None)
    ip = getattr(laddr, "ip", None)
    port = getattr(laddr, "port", None)
    if ip is not None and port is not None:
        return f"{ip}:{port}"
    if isinstance(laddr, tuple) and len(laddr) >= 2:
        return f"{laddr[0]}:{laddr[1]}"
    return None


def _process_name(pid: int | None) -> str | None:
    if pid is None:
        return None
    try:
        return str(psutil.Process(pid).name())
    except Exception:
        return None
