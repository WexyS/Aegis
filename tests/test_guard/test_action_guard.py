"""
Test: Action Guard — Security gate.
"""

from __future__ import annotations

from aegis.core.config import PROJECT_ROOT
from aegis.core.constants import RiskLevel, IntentSource
from aegis.core.schemas import IntentResult
from aegis.guard.action_guard import ActionGuard


class TestGuard:
    def setup_method(self) -> None:
        self.guard = ActionGuard()

    def test_allows_low_risk(self) -> None:
        intent = IntentResult(intent="open_url", confidence=1.0, params={"url": "https://google.com"}, risk=RiskLevel.LOW, raw_input="google aç")
        r = self.guard.evaluate(intent)
        assert r.allowed is True

    def test_blocks_unknown(self) -> None:
        intent = IntentResult(intent="unknown", confidence=0.0, params={}, risk=RiskLevel.NONE, raw_input="xyzzy")
        r = self.guard.evaluate(intent)
        assert r.allowed is False

    def test_blocks_excessive_clicks(self) -> None:
        intent = IntentResult(intent="click", confidence=1.0, params={"count": 50}, risk=RiskLevel.MEDIUM, raw_input="50 kere tıkla")
        r = self.guard.evaluate(intent)
        assert r.allowed is False

    def test_allows_normal_clicks(self) -> None:
        intent = IntentResult(intent="click", confidence=1.0, params={"count": 5}, risk=RiskLevel.MEDIUM, raw_input="5 kere tıkla")
        r = self.guard.evaluate(intent)
        assert r.allowed is True

    def test_warns_on_medium_risk(self) -> None:
        intent = IntentResult(intent="click", confidence=1.0, params={"count": 3}, risk=RiskLevel.MEDIUM, raw_input="3 kere tıkla")
        r = self.guard.evaluate(intent)
        assert r.allowed is True
        assert any("Medium risk" in w for w in r.warnings)

    def test_blocks_bad_url_scheme(self) -> None:
        intent = IntentResult(intent="open_url", confidence=1.0, params={"url": "file:///etc/passwd"}, risk=RiskLevel.LOW, raw_input="test")
        r = self.guard.evaluate(intent)
        assert r.allowed is False

    def test_blocks_empty_url(self) -> None:
        intent = IntentResult(intent="open_url", confidence=1.0, params={}, risk=RiskLevel.LOW, raw_input="test")
        r = self.guard.evaluate(intent)
        assert r.allowed is False

    def test_blocks_mutating_git_actions(self) -> None:
        intent = IntentResult(intent="git_action", confidence=1.0, params={"git_cmd": "push"}, risk=RiskLevel.MEDIUM, raw_input="git push")
        r = self.guard.evaluate(intent)
        assert r.allowed is False
        assert r.risk == RiskLevel.CRITICAL

    def test_blocks_write_file_to_forbidden_path(self) -> None:
        intent = IntentResult(
            intent="write_file",
            confidence=1.0,
            params={"path": "c:\\windows\\temp\\aegis-test.txt", "content": "nope"},
            risk=RiskLevel.MEDIUM,
            raw_input="write nope to c:\\windows\\temp\\aegis-test.txt",
        )
        r = self.guard.evaluate(intent)
        assert r.allowed is False
        assert r.risk == RiskLevel.CRITICAL

    def test_blocks_write_file_outside_allowed_roots(self, tmp_path) -> None:
        intent = IntentResult(
            intent="write_file",
            confidence=1.0,
            params={"path": str(tmp_path / "outside.txt"), "content": "nope"},
            risk=RiskLevel.MEDIUM,
            raw_input="write nope to outside",
        )
        r = self.guard.evaluate(intent)
        assert r.allowed is False
        assert r.risk == RiskLevel.CRITICAL

    def test_allows_write_file_inside_project_root_with_approval(self) -> None:
        intent = IntentResult(
            intent="write_file",
            confidence=1.0,
            params={"path": str(PROJECT_ROOT / "scratch" / "ok.txt"), "content": "ok"},
            risk=RiskLevel.MEDIUM,
            raw_input="write ok to scratch/ok.txt",
        )
        r = self.guard.evaluate(intent)
        assert r.allowed is True
        assert r.requires_approval is True

    def test_allows_read_only_git_status(self) -> None:
        intent = IntentResult(intent="git_action", confidence=1.0, params={"git_cmd": "status"}, risk=RiskLevel.LOW, raw_input="git status")
        r = self.guard.evaluate(intent)
        assert r.allowed is True
