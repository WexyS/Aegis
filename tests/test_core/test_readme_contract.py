from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_readme_declares_reliability_and_simplicity_constraints() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Reliability Budget" in readme
    assert "Operational Simplicity Budget" in readme
    assert "Human Understandability Constraint" in readme
    assert "No fake systems" in readme
    assert "Reliable AI Computer Operator" in readme
