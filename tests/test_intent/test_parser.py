"""
Test: Intent Parser — Determinism, Turkish commands, click support.
"""

from __future__ import annotations

import pytest
from aegis.core.constants import RiskLevel, IntentSource
from aegis.intent.parser import IntentParser


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

    async def test_close_notepad(self) -> None:
        r = await self.parser.parse("notepad kapat")
        assert r[0].intent == "close_app"
        assert r[0].risk == RiskLevel.MEDIUM
        assert r[0].params["app"] == "notepad"

    async def test_generic_open_app_name_is_preserved_for_registry_resolution(self) -> None:
        r = await self.parser.parse("open steam")

        assert r[0].intent == "open_app"
        assert r[0].risk == RiskLevel.MEDIUM
        assert r[0].params["app"] == "steam"
