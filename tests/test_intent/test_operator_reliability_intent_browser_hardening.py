from __future__ import annotations

import pytest

from aegis.core.browser_preferences import BrowserPreferenceResolution
from aegis.core.config import load_settings
from aegis.core.constants import RiskLevel
from aegis.guard.action_guard import ActionGuard
from aegis.intent.parser import IntentParser


@pytest.fixture(autouse=True)
def deterministic_decomposition_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ENABLE_DETERMINISTIC_DECOMPOSITION", raising=False)
    load_settings(force_reload=True)
    yield
    monkeypatch.delenv("ENABLE_DETERMINISTIC_DECOMPOSITION", raising=False)
    load_settings(force_reload=True)


async def _parse(text: str):
    return await IntentParser().parse(text)


def _fake_brave_preference(explicit_browser=None, prog_id_reader=None):
    return BrowserPreferenceResolution(
        browser_app=explicit_browser or "brave",
        browser_runtime="controlled_browser",
        detection_source="test",
        configured=True,
        controlled_browser=True,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("text", "app"),
    [
        ("notepad a\u00e7", "notepad"),
        ("brave a\u00e7", "brave"),
        ("open notepad", "notepad"),
        ("open brave", "brave"),
    ],
)
async def test_turkish_and_english_known_app_launches_remain_app_intents(text: str, app: str) -> None:
    results = await _parse(text)

    assert [result.intent for result in results] == ["open_app"]
    assert results[0].params["app"] == app
    assert results[0].params.get("_app_known") is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("text", "query", "preferred_browser"),
    [
        ("brave a\u00e7 python nedir diye arat", "python nedir", "brave"),
        ("brave'de python nedir ara", "python nedir", "brave"),
        ("open brave and search python nedir", "python nedir", "brave"),
        ("search python nedir", "python nedir", None),
        ("python nedir diye arat", "python nedir", None),
    ],
)
async def test_turkish_and_english_search_routes_as_browser_search(
    monkeypatch: pytest.MonkeyPatch,
    text: str,
    query: str,
    preferred_browser: str | None,
) -> None:
    monkeypatch.setattr("aegis.intent.decomposition.resolve_preferred_browser", _fake_brave_preference)

    results = await _parse(text)

    assert [result.intent for result in results] == ["search_web"]
    assert results[0].params["query"] == query
    assert results[0].params["search_provider"] == "google"
    assert results[0].params["browser_runtime"] == "controlled_browser"
    assert results[0].params["controlled_browser"] is True
    assert results[0].metadata["route_kind"] == "browser_search"
    assert results[0].metadata["search_provider"] == "google"
    assert results[0].metadata["browser_runtime"] == "controlled_browser"
    assert results[0].metadata["controlled_browser"] is True
    if preferred_browser:
        assert results[0].params["preferred_browser"] == preferred_browser
    else:
        assert results[0].params["preferred_browser"] == "brave"
    assert "app" not in results[0].params


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("text", "url", "site"),
    [
        ("githuba gir", "https://github.com", "github"),
        ("github a\u00e7", "https://github.com", "github"),
        ("open github", "https://github.com", "github"),
        ("google a\u00e7", "https://www.google.com", "google"),
    ],
)
async def test_known_sites_route_as_open_url_not_open_app(
    monkeypatch: pytest.MonkeyPatch,
    text: str,
    url: str,
    site: str,
) -> None:
    monkeypatch.setattr("aegis.intent.decomposition.resolve_preferred_browser", _fake_brave_preference)

    results = await _parse(text)

    assert [result.intent for result in results] == ["open_url"]
    assert results[0].params["url"] == url
    assert results[0].params["site"] == site
    assert results[0].metadata["route_kind"] == "browser_open"
    assert results[0].params["preferred_browser"] == "brave"
    assert "app" not in results[0].params


@pytest.mark.asyncio
async def test_google_search_provider_is_not_chrome_browser_app(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("aegis.intent.decomposition.resolve_preferred_browser", _fake_brave_preference)

    results = await _parse("google a\u00e7\u0131p github yaz")

    assert [result.intent for result in results] == ["search_web"]
    assert results[0].params["query"] == "github"
    assert results[0].params["search_provider"] == "google"
    assert results[0].params["preferred_browser"] == "brave"
    assert results[0].params["browser"] == "brave"
    assert results[0].params.get("app") is None
    assert results[0].metadata["route_kind"] == "browser_search"
    assert results[0].metadata["search_provider"] == "google"


@pytest.mark.asyncio
async def test_plain_turkish_write_phrase_does_not_become_browser_search() -> None:
    results = await _parse("merhaba yaz")

    assert [result.intent for result in results] == ["type"]
    assert results[0].params["text"] == "merhaba"
    assert results[0].metadata.get("route_kind") != "browser_search"


@pytest.mark.asyncio
async def test_search_phrase_never_becomes_executable_app_target() -> None:
    results = await _parse("python nedir diye arat")

    assert [result.intent for result in results] == ["search_web"]
    assert results[0].params["query"] == "python nedir"
    assert results[0].params.get("app") is None


@pytest.mark.asyncio
async def test_mixed_destructive_command_blocks_before_partial_open() -> None:
    results = await _parse("notepad a\u00e7 sonra dosya sil")

    assert [result.intent for result in results] == ["unknown"]
    assert results[0].risk == RiskLevel.NONE
    assert results[0].metadata["plan_status"] == "blocked"
    assert "mixed destructive command blocked before partial execution" in results[0].metadata["guard_notes"]


@pytest.mark.asyncio
async def test_unknown_app_alias_is_not_allowed_by_guard() -> None:
    results = await _parse("open totally unknown app")

    assert [result.intent for result in results] == ["open_app"]
    assert results[0].params["_app_known"] is False
    decision = ActionGuard().evaluate(results[0])
    assert decision.allowed is False
    assert "Unknown or query-like app target" in decision.reason
