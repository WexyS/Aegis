from __future__ import annotations

from aegis.core.browser_preferences import browser_app_from_progid, resolve_preferred_browser


def test_browser_app_from_windows_progid_maps_known_browsers() -> None:
    assert browser_app_from_progid("BraveHTML") == "brave"
    assert browser_app_from_progid("ChromeHTML") == "chrome"
    assert browser_app_from_progid("MSEdgeHTM") == "edge"
    assert browser_app_from_progid("FirefoxURL-308046B0AF4A39CB") == "firefox"


def test_resolve_preferred_browser_uses_explicit_browser_as_metadata_only() -> None:
    result = resolve_preferred_browser(explicit_browser="brave", prog_id_reader=lambda: "ChromeHTML")

    assert result.browser_app == "brave"
    assert result.browser_runtime == "controlled_browser"
    assert result.controlled_browser is True
    assert result.detection_source == "explicit"
    assert result.configured is True
    assert result.warning is None


def test_resolve_preferred_browser_reads_default_browser_without_launch_proof() -> None:
    result = resolve_preferred_browser(prog_id_reader=lambda: "BraveHTML")

    assert result.browser_app == "brave"
    assert result.browser_runtime == "controlled_browser"
    assert result.controlled_browser is True
    assert result.detection_source == "windows_registry"
    assert result.configured is True
    assert result.warning is None


def test_resolve_preferred_browser_unknown_default_stays_controlled_unavailable() -> None:
    result = resolve_preferred_browser(prog_id_reader=lambda: "UnknownBrowserHTML")

    assert result.browser_app is None
    assert result.browser_runtime == "controlled_browser"
    assert result.controlled_browser is True
    assert result.detection_source == "unavailable"
    assert result.configured is False
    assert result.warning == "default_browser_unavailable"
