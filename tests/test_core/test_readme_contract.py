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


def test_readme_declares_contract_versioning_policy() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Contract Versioning Policy" in readme
    assert "They are not roadmap phase labels" in readme
    assert "Additive fields can stay on the same contract version" in readme
    assert "Breaking payload, verifier, or replay semantics require a new version" in readme
    assert "Old journal events and snapshots must remain readable" in readme
    assert "must not infer success or synthesize data when it sees an unknown version" in readme


def test_readme_declares_action_proposal_contract() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Action Proposals and Maintenance Actions" in readme
    assert "backend-owned action proposals" in readme
    assert "affected resources" in readme
    assert "approval text" in readme
    assert "create_logging_directory" in readme
    assert "maintenance-action-verifier/1" in readme
