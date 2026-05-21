"""
Test: Intent Parser — Determinism, Turkish commands, click support.
"""

from __future__ import annotations

import pytest
from aegis.core.constants import RiskLevel, IntentSource
from aegis.core.config import load_settings
from aegis.intent.parser import IntentParser


def _set_deterministic_decomposition(monkeypatch: pytest.MonkeyPatch, enabled: bool) -> None:
    monkeypatch.setenv("ENABLE_DETERMINISTIC_DECOMPOSITION", "true" if enabled else "false")
    load_settings(force_reload=True)


@pytest.mark.asyncio
class TestDeterminism:
    """Same input → same output, always."""

    def setup_method(self) -> None:
        self.parser = IntentParser()

    async def test_same_input_same_output(self) -> None:
        r1 = await self.parser.parse("google aç")
        r2 = await self.parser.parse("google aç")
        assert r1[0].intent == r2[0].intent
        assert r1[0].params == r2[0].params
        assert r1[0].confidence == r2[0].confidence

    async def test_source_is_always_rule(self) -> None:
        res = await self.parser.parse("google aç")
        assert res[0].source == IntentSource.RULE


@pytest.mark.asyncio
class TestUnknownHandling:
    """Unknown → 'unknown', NEVER guess."""

    def setup_method(self) -> None:
        self.parser = IntentParser()

    async def test_gibberish(self) -> None:
        # Note: If AI is enabled and Ollama is running, this might return AI results.
        # But for base testing, it should at least return results.
        r = await self.parser.parse("xyzzy foobar baz")
        assert len(r) >= 1
        # If AI failed or returned unknown:
        assert r[0].intent in ["unknown", "general_chat"]

    async def test_empty(self) -> None:
        r = await self.parser.parse("")
        assert r[0].intent == "unknown"


@pytest.mark.asyncio
class TestOpenUrl:
    def setup_method(self) -> None:
        self.parser = IntentParser()

    async def test_google_ac_turkish_order(self) -> None:
        r = await self.parser.parse("google aç")
        assert r[0].intent == "open_url"
        assert r[0].params["url"] == "https://www.google.com"

    async def test_explicit_url(self) -> None:
        r = await self.parser.parse("aç https://example.com")
        assert r[0].intent == "open_url"
        assert r[0].params["url"] == "https://example.com"
    async def test_explicit_url_with_real_turkish_ac(self) -> None:
        r = await self.parser.parse("aç https://example.com")
        assert r[0].intent == "open_url"
        assert r[0].params["url"] == "https://example.com"

    async def test_google_ac_with_real_turkish_ac(self) -> None:
        r = await self.parser.parse("google aç")
        assert r[0].intent == "open_url"
        assert r[0].params["url"] == "https://www.google.com"

@pytest.mark.asyncio
class TestWriteFile:
    def setup_method(self) -> None:
        self.parser = IntentParser()

    async def test_save_extracts_path_and_content(self) -> None:
        r = await self.parser.parse("save smoke-live to scratch/aegis_write_smoke.txt")

        assert r[0].intent == "write_file"
        assert r[0].params["path"] == "scratch/aegis_write_smoke.txt"
        assert r[0].params["content"] == "smoke-live"

    async def test_write_extracts_path_and_content(self) -> None:
        r = await self.parser.parse("write smoke-live to scratch/aegis_write_smoke.txt")

        assert r[0].intent == "write_file"
        assert r[0].params["path"] == "scratch/aegis_write_smoke.txt"
        assert r[0].params["content"] == "smoke-live"

    async def test_write_file_to_windows_path_parses_as_critical(self) -> None:
        r = await self.parser.parse("write nope to c:\\windows\\temp\\aegis-test.txt")

        assert r[0].intent == "write_file"
        assert r[0].risk == RiskLevel.CRITICAL


@pytest.mark.asyncio
class TestClick:
    def setup_method(self) -> None:
        self.parser = IntentParser()

    async def test_5_kere_tikla(self) -> None:
        r = await self.parser.parse("5 kere tıkla")
        assert r[0].intent == "click"
        assert r[0].params["count"] == 5

    async def test_single_tikla(self) -> None:
        r = await self.parser.parse("tıkla")
        assert r[0].intent == "click"
        assert r[0].params["count"] == 1


@pytest.mark.asyncio
class TestMultiStep:
    def setup_method(self) -> None:
        self.parser = IntentParser()

    async def test_chain_ve(self) -> None:
        r = await self.parser.parse("google aç ve python ara")
        assert len(r) == 2
        assert r[0].intent == "open_url"
        assert r[1].intent == "search_web"

    async def test_chain_sonra(self) -> None:
        r = await self.parser.parse("notepad aç sonra merhaba yaz")
        assert len(r) == 2
        assert r[0].intent == "open_app"
        assert r[1].intent == "type"

    async def test_compound_browser_search_decomposes_app_and_query(self) -> None:
        r = await self.parser.parse("brave i açıp python nedir araması yap")

        assert len(r) == 2
        assert r[0].intent == "open_app"
        assert r[0].params["app"] == "brave"
        assert r[0].params["_process_name"] == "brave.exe"
        assert r[1].intent == "search_web"
        assert r[1].params["query"] == "python nedir"
        assert r[1].params["browser"] == "brave"

    async def test_mixed_known_and_unknown_segments_are_not_silently_dropped(self) -> None:
        r = await self.parser.parse("notepad aç sonra xyzzy foobar baz")

        assert len(r) == 2
        assert r[0].intent == "open_app"
        assert r[1].intent == "unknown"


@pytest.mark.asyncio
class TestOther:
    def setup_method(self) -> None:
        self.parser = IntentParser()

    async def test_hello(self) -> None:
        r = await self.parser.parse("merhaba")
        assert r[0].intent == "general_chat"


@pytest.mark.asyncio
class TestGitAction:
    def setup_method(self) -> None:
        self.parser = IntentParser()

    async def test_git_status_is_low_risk(self) -> None:
        r = await self.parser.parse("git status")

        assert r[0].intent == "git_action"
        assert r[0].params["git_cmd"] == "status"
        assert r[0].risk == RiskLevel.LOW


@pytest.mark.asyncio
class TestAppLifecycle:
    def setup_method(self) -> None:
        self.parser = IntentParser()

    async def test_focus_notepad(self) -> None:
        r = await self.parser.parse("notepad'e odaklan")
        assert r[0].intent == "focus_app"
        assert r[0].risk == RiskLevel.MEDIUM
        assert r[0].params["app"] == "notepad"
        assert r[0].params["_process_name"] == "notepad.exe"
        assert "Notepad" in r[0].params["_keywords"]

    async def test_close_notepad(self) -> None:
        r = await self.parser.parse("notepad kapat")
        assert r[0].intent == "close_app"
        assert r[0].risk == RiskLevel.MEDIUM
        assert r[0].params["app"] == "notepad"
        assert r[0].params["_process_name"] == "notepad.exe"

    async def test_generic_close_app_name_is_preserved_for_registry_resolution(self) -> None:
        r = await self.parser.parse("discord u kapat")

        assert r[0].intent == "close_app"
        assert r[0].risk == RiskLevel.MEDIUM
        assert r[0].params["app"] == "discord"

    async def test_generic_open_app_name_is_preserved_for_registry_resolution(self) -> None:
        r = await self.parser.parse("open steam")

        assert r[0].intent == "open_app"
        assert r[0].risk == RiskLevel.MEDIUM
        assert r[0].params["app"] == "steam"


@pytest.mark.asyncio
class TestTurkishAliasEncoding:
    def setup_method(self) -> None:
        self.parser = IntentParser()

    @pytest.mark.parametrize(
        ("text", "app", "process_name"),
        [
            ("tarayıcı aç", "chrome", "chrome.exe"),
            ("brave tarayıcı aç", "brave", "brave.exe"),
            ("google chrome aç", "chrome", "chrome.exe"),
            ("not defteri aç", "notepad", "notepad.exe"),
            ("hesap makinesi aç", "calc", "CalculatorApp.exe"),
        ],
    )
    async def test_turkish_and_browser_aliases_open_expected_app(
        self,
        text: str,
        app: str,
        process_name: str,
    ) -> None:
        r = await self.parser.parse(text)

        assert [item.intent for item in r] == ["open_app"]
        assert r[0].params["app"] == app
        assert r[0].params["_process_name"] == process_name


@pytest.mark.asyncio
class TestDeterministicDecompositionWiring:
    def setup_method(self) -> None:
        self.parser = IntentParser()

    async def test_feature_flag_off_keeps_open_type_legacy_behavior(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_deterministic_decomposition(monkeypatch, False)

        r = await self.parser.parse("notepad açıp merhaba yaz")

        assert [item.intent for item in r] == ["open_app"]
        assert all(item.metadata.get("decomposition") != "deterministic" for item in r)

    async def test_feature_flag_off_keeps_open_search_legacy_behavior(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_deterministic_decomposition(monkeypatch, False)

        r = await self.parser.parse("brave açıp python nedir ara")

        assert [item.intent for item in r] == ["open_app", "search_web"]
        assert all(item.metadata.get("decomposition") != "deterministic" for item in r)

    async def test_feature_flag_on_routes_open_type_through_deterministic_decomposition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_deterministic_decomposition(monkeypatch, True)

        r = await self.parser.parse("notepad açıp merhaba yaz")

        assert [item.intent for item in r] == ["open_app", "type"]
        assert r[1].params["_require_focus"] == "notepad"
        assert r[0].metadata["decomposition"] == "deterministic"
        assert r[0].metadata["step_index"] == 0
        assert r[0].metadata["step_count"] == 2
        assert r[0].metadata["source_span"] == "notepad"

    async def test_feature_flag_on_routes_open_search_through_deterministic_decomposition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_deterministic_decomposition(monkeypatch, True)

        r = await self.parser.parse("brave açıp python nedir ara")

        assert [item.intent for item in r] == ["open_app", "search_web"]
        assert r[1].params["browser"] == "brave"
        assert r[1].metadata["decomposition"] == "deterministic"
        assert r[1].metadata["step_index"] == 1

    async def test_feature_flag_on_unrelated_text_falls_back_to_existing_parser(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_deterministic_decomposition(monkeypatch, True)

        r = await self.parser.parse("merhaba")

        assert r[0].intent == "general_chat"
        assert r[0].metadata.get("decomposition") != "deterministic"

    async def test_feature_flag_on_unknown_open_type_returns_non_executable_unknown(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_deterministic_decomposition(monkeypatch, True)

        r = await self.parser.parse("unknownapp aç ve merhaba yaz")

        assert len(r) == 1
        assert r[0].intent == "unknown"
        assert r[0].metadata["decomposition"] == "deterministic"
        assert r[0].metadata["plan_status"] == "clarification_required"
        assert r[0].metadata["ambiguities"] == ["unknown app for open+type: unknownapp"]

    async def test_feature_flag_on_unknown_open_search_returns_non_executable_unknown(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_deterministic_decomposition(monkeypatch, True)

        r = await self.parser.parse("unknownapp aç ve python ara")

        assert len(r) == 1
        assert r[0].intent == "unknown"
        assert r[0].metadata["decomposition"] == "deterministic"
        assert r[0].metadata["plan_status"] == "clarification_required"
        assert r[0].metadata["ambiguities"] == ["unknown app for open+search: unknownapp"]

    async def test_feature_flag_on_ambiguous_click_does_not_execute_or_fall_back(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_deterministic_decomposition(monkeypatch, True)

        r = await self.parser.parse("brave aç ve ilk sonuca tıkla")

        assert len(r) == 1
        assert r[0].intent == "unknown"
        assert r[0].metadata["decomposition"] == "deterministic"
        assert r[0].metadata["plan_status"] == "clarification_required"

    async def test_feature_flag_on_adapter_failure_returns_blocked_unknown(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_deterministic_decomposition(monkeypatch, True)

        def boom(*args, **kwargs):
            raise ValueError("adapter exploded")

        monkeypatch.setattr("aegis.intent.parser.normalized_plan_to_intents", boom)

        r = await self.parser.parse("notepad açıp merhaba yaz")

        assert len(r) == 1
        assert r[0].intent == "unknown"
        assert r[0].metadata["decomposition"] == "deterministic"
        assert r[0].metadata["plan_status"] == "blocked"
        assert "adapter exploded" in r[0].metadata["guard_notes"]
