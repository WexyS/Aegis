from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


# Centralized Application Registry with Window and Process Metadata.
APP_REGISTRY: dict[str, dict] = {
    "premiere": {
        "path": r"C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
        "process_name": "Adobe Premiere Pro.exe",
        "aliases": ["premiere", "adobe premiere", "premier", "video editor"],
        "fallback": None,
        "window_keywords": ["Adobe Premiere Pro", "Premiere"]
    },
    "photoshop": {
        "path": r"C:\Program Files\Adobe\Adobe Photoshop 2026\Photoshop.exe",
        "process_name": "Photoshop.exe",
        "aliases": ["photoshop", "adobe photoshop"],
        "fallback": "premiere",
        "window_keywords": ["Adobe Photoshop", "Photoshop"]
    },
    "notepad": {
        "path": "notepad.exe",
        "process_name": "notepad.exe",
        "aliases": ["not defteri", "notepad"],
        "fallback": None,
        "window_keywords": ["Notepad", "Not Defteri"]
    },
    "calc": {
        "path": "calc.exe",
        "process_name": "CalculatorApp.exe",
        "aliases": ["hesap makinesi", "calc", "calculator"],
        "fallback": None,
        "window_keywords": ["Calculator", "Hesap Makinesi"]
    },
    "chrome": {
        "path": "chrome.exe",
        "process_name": "chrome.exe",
        "aliases": ["chrome", "google chrome", "browser", "tarayıcı"],
        "fallback": None,
        "window_keywords": ["Google Chrome", "New Tab"]
    }
}

_discovered_registry: dict[str, dict] = {}


@dataclass(frozen=True)
class AppDiscoveryRoots:
    start_menu_dirs: list[Path] = field(default_factory=list)
    desktop_dirs: list[Path] = field(default_factory=list)
    program_dirs: list[Path] = field(default_factory=list)
    steam_dirs: list[Path] = field(default_factory=list)
    epic_manifest_dirs: list[Path] = field(default_factory=list)


def default_discovery_roots() -> AppDiscoveryRoots:
    program_data = Path(os.environ.get("ProgramData", r"C:\ProgramData"))
    app_data = Path(os.environ.get("AppData", ""))
    user_profile = Path(os.environ.get("USERPROFILE", ""))
    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    program_files_x86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))

    return AppDiscoveryRoots(
        start_menu_dirs=[
            program_data / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            app_data / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        ],
        desktop_dirs=[
            user_profile / "Desktop",
            Path(os.environ.get("Public", r"C:\Users\Public")) / "Desktop",
        ],
        program_dirs=[program_files, program_files_x86],
        steam_dirs=[program_files_x86 / "Steam", program_files / "Steam"],
        epic_manifest_dirs=[
            program_data / "Epic" / "EpicGamesLauncher" / "Data" / "Manifests",
        ],
    )


def resolve_app_name(name: str) -> str | None:
    if not name:
        return None
    query = _normalize_key(name)
    for key, val in _all_registry_items():
        aliases = [_normalize_key(alias) for alias in val.get("aliases", [])]
        if query == _normalize_key(key) or query in aliases:
            return key
    return None


def get_app_config(name: str):
    key = resolve_app_name(name) or _normalize_key(name)
    return APP_REGISTRY.get(key) or _discovered_registry.get(key)


def all_app_configs() -> dict[str, dict]:
    merged = dict(APP_REGISTRY)
    merged.update(_discovered_registry)
    return merged


def discover_installed_apps(roots: AppDiscoveryRoots | None = None, *, limit: int = 500) -> dict[str, dict]:
    roots = roots or default_discovery_roots()
    discovered: dict[str, dict] = {}

    _scan_shortcut_dirs(roots.start_menu_dirs, discovered, limit=limit, max_depth=8)
    _scan_shortcut_dirs(roots.desktop_dirs, discovered, limit=limit, max_depth=1)
    _scan_program_dirs(roots.program_dirs, discovered, limit=limit)
    _scan_steam_dirs(roots.steam_dirs, discovered, limit=limit)
    _scan_epic_manifests(roots.epic_manifest_dirs, discovered, limit=limit)

    return discovered


def refresh_installed_app_registry(roots: AppDiscoveryRoots | None = None) -> dict[str, dict]:
    global _discovered_registry
    _discovered_registry = discover_installed_apps(roots)
    return get_app_registry_snapshot()


def get_app_registry_snapshot(limit: int = 200) -> dict:
    entries = []
    for app_id, config in sorted(all_app_configs().items()):
        entries.append({
            "app_id": app_id,
            "display_name": config.get("display_name") or _display_name(app_id),
            "source": config.get("source", "configured"),
            "aliases": list(config.get("aliases", [])),
            "process_name": config.get("process_name"),
            "launch_target_type": _launch_target_type(str(config.get("path", ""))),
        })

    return {
        "scan_version": "app-registry/1",
        "configured_count": len(APP_REGISTRY),
        "discovered_count": len(_discovered_registry),
        "entry_count": len(entries),
        "entries": entries[:limit],
        "truncated": len(entries) > limit,
    }


def _scan_shortcut_dirs(paths: Iterable[Path], discovered: dict[str, dict], *, limit: int, max_depth: int) -> None:
    for base in paths:
        for shortcut in _iter_files(base, (".lnk", ".url"), max_depth=max_depth):
            if len(discovered) >= limit:
                return
            display = shortcut.stem.strip()
            key = _normalize_key(display)
            if not key:
                continue
            discovered.setdefault(key, {
                "path": str(shortcut),
                "process_name": None,
                "aliases": _aliases_for(display),
                "fallback": None,
                "window_keywords": [display],
                "display_name": display,
                "source": "start_menu",
            })


def _scan_program_dirs(paths: Iterable[Path], discovered: dict[str, dict], *, limit: int) -> None:
    ignored = {"unins", "uninstall", "uninstaller", "setup", "update", "updater"}
    for base in paths:
        if not base.exists():
            continue
        try:
            candidates = [item for item in base.iterdir() if item.is_dir()]
        except OSError:
            continue
        for app_dir in candidates:
            try:
                executables = [item for item in app_dir.iterdir() if item.is_file() and item.suffix.lower() == ".exe"]
            except OSError:
                continue
            for exe in executables:
                if len(discovered) >= limit:
                    return
                stem = exe.stem.strip()
                lower = stem.lower()
                if any(token in lower for token in ignored):
                    continue
                key = _normalize_key(stem)
                if not key:
                    continue
                discovered.setdefault(key, {
                    "path": str(exe),
                    "process_name": exe.name,
                    "aliases": _aliases_for(stem),
                    "fallback": None,
                    "window_keywords": [stem],
                    "display_name": stem,
                    "source": "program_files",
                })


def _scan_steam_dirs(paths: Iterable[Path], discovered: dict[str, dict], *, limit: int) -> None:
    for steam_dir in paths:
        steamapps = steam_dir / "steamapps"
        for manifest in _iter_files(steamapps, (".acf",), max_depth=1):
            if len(discovered) >= limit:
                return
            text = _read_text(manifest)
            appid = _acf_value(text, "appid") or manifest.stem.replace("appmanifest_", "")
            name = _acf_value(text, "name")
            if not appid or not name:
                continue
            key = _normalize_key(name)
            discovered.setdefault(key, {
                "path": f"steam://rungameid/{appid}",
                "process_name": None,
                "aliases": _aliases_for(name),
                "fallback": "steam",
                "window_keywords": [name],
                "display_name": name,
                "source": "steam",
            })


def _scan_epic_manifests(paths: Iterable[Path], discovered: dict[str, dict], *, limit: int) -> None:
    for manifest_dir in paths:
        for manifest in _iter_files(manifest_dir, (".item",), max_depth=1):
            if len(discovered) >= limit:
                return
            try:
                data = json.loads(manifest.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            name = str(data.get("DisplayName") or "").strip()
            app_name = str(data.get("AppName") or "").strip()
            install = str(data.get("InstallLocation") or "").strip()
            launch_exe = str(data.get("LaunchExecutable") or "").strip()
            if not name:
                continue
            target = f"com.epicgames.launcher://apps/{app_name}?action=launch&silent=true" if app_name else ""
            process_name = None
            if install and launch_exe:
                exe = Path(install) / launch_exe
                if exe.exists():
                    target = str(exe)
                    process_name = exe.name
            if not target:
                continue
            key = _normalize_key(name)
            discovered.setdefault(key, {
                "path": target,
                "process_name": process_name,
                "aliases": _aliases_for(name),
                "fallback": "epic games launcher",
                "window_keywords": [name],
                "display_name": name,
                "source": "epic",
            })


def _iter_files(base: Path, suffixes: tuple[str, ...], *, max_depth: int):
    if not base or not base.exists():
        return
    try:
        stack = [(base, 0)]
        while stack:
            current, depth = stack.pop()
            if depth > max_depth:
                continue
            try:
                for item in current.iterdir():
                    if item.is_file() and item.suffix.lower() in suffixes:
                        yield item
                    elif item.is_dir() and depth < max_depth:
                        stack.append((item, depth + 1))
            except OSError:
                continue
    except OSError:
        return


def _all_registry_items():
    yield from APP_REGISTRY.items()
    yield from _discovered_registry.items()


def _normalize_key(value: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", clean).strip()


def _aliases_for(display: str) -> list[str]:
    aliases = []
    for value in (display.lower().strip(), _normalize_key(display)):
        if value and value not in aliases:
            aliases.append(value)
    return aliases


def _display_name(app_id: str) -> str:
    return " ".join(part.capitalize() for part in app_id.split())


def _launch_target_type(target: str) -> str:
    if target.startswith("steam://"):
        return "steam_uri"
    if target.startswith("com.epicgames.launcher://"):
        return "epic_uri"
    if target.lower().endswith(".lnk"):
        return "shortcut"
    if target.lower().endswith(".url"):
        return "url_shortcut"
    if target.lower().endswith(".exe"):
        return "executable"
    return "unknown"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _acf_value(text: str, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s+"([^"]+)"', text)
    return match.group(1).strip() if match else None
