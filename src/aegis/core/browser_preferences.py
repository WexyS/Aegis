from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from aegis.core.app_map import resolve_app_name


DEFAULT_BROWSER_REGISTRY_PATH = (
    r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice"
)


@dataclass(frozen=True)
class BrowserPreferenceResolution:
    browser_app: str | None
    browser_runtime: str
    detection_source: str
    prog_id: str | None = None
    configured: bool = False
    controlled_browser: bool = True
    warning: str | None = None


def browser_app_from_progid(prog_id: str | None) -> str | None:
    value = (prog_id or "").strip().lower()
    if not value:
        return None
    if "brave" in value:
        return "brave"
    if "chrome" in value:
        return "chrome"
    if "msedge" in value or "edge" in value:
        return "edge"
    if "firefox" in value:
        return "firefox"
    return None


def read_windows_default_browser_progid() -> str | None:
    try:
        import winreg
    except ImportError:
        return None

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DEFAULT_BROWSER_REGISTRY_PATH) as key:
            value, _ = winreg.QueryValueEx(key, "ProgId")
            return str(value) if value else None
    except OSError:
        return None


def resolve_preferred_browser(
    *,
    explicit_browser: str | None = None,
    prog_id_reader: Callable[[], str | None] | None = None,
) -> BrowserPreferenceResolution:
    """Resolve a browser preference without launching or mutating anything.

    Aegis web tools currently use a controlled Playwright browser. The returned
    browser_app is preference metadata only; it is not execution proof.
    """

    if explicit_browser:
        browser = browser_app_from_progid(explicit_browser) or explicit_browser.strip().lower()
        configured = resolve_app_name(browser) is not None
        return BrowserPreferenceResolution(
            browser_app=browser,
            browser_runtime="controlled_browser",
            detection_source="explicit",
            prog_id=None,
            configured=configured,
            controlled_browser=True,
            warning=None if configured else "explicit_browser_unconfigured",
        )

    reader = prog_id_reader or read_windows_default_browser_progid
    prog_id = reader()
    browser = browser_app_from_progid(prog_id)
    if browser:
        configured = resolve_app_name(browser) is not None
        return BrowserPreferenceResolution(
            browser_app=browser,
            browser_runtime="controlled_browser",
            detection_source="windows_registry",
            prog_id=prog_id,
            configured=configured,
            controlled_browser=True,
            warning=None if configured else "detected_browser_unconfigured",
        )

    return BrowserPreferenceResolution(
        browser_app=None,
        browser_runtime="controlled_browser",
        detection_source="unavailable",
        prog_id=prog_id,
        configured=False,
        controlled_browser=True,
        warning="default_browser_unavailable",
    )
