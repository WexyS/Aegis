from __future__ import annotations

from copy import deepcopy

import pytest

from aegis.core.capability_broker import CONTRACT_NAME, NO_ACTION_FLAGS, build_capability_assessment
from aegis.core.operator_auto_router import build_operator_route_preview


@pytest.mark.parametrize(
    ("prompt", "classification"),
    (
        ("Aegis runtime status and active blockers", "observe_only"),
        ("Explain the current model boundary", "explain_only"),
        ("Draft a safe sprint plan", "proposal_only"),
        ("Review approval requirements for this action", "approval_required"),
        ("Run this shell command", "execution_unavailable"),
        ("Open the browser and visit this website", "execution_unavailable"),
        ("Create a file in this folder", "execution_unavailable"),
        ("Use Moonshot Kimi through the cloud", "provider_unavailable"),
        ("Pineapple constellation", "unsupported_or_ambiguous"),
    ),
)
def test_capability_assessment_is_deterministic(prompt: str, classification: str) -> None:
    first = build_operator_route_preview(prompt)["capability_assessment"]
    second = build_operator_route_preview(prompt)["capability_assessment"]

    assert first == second
    assert first["classification"] == classification
    assert first["contract"] == CONTRACT_NAME


def test_capability_assessment_preserves_non_authority_contract() -> None:
    assessment = build_operator_route_preview("Draft a safe plan")["capability_assessment"]

    assert assessment["read_only"] is True
    assert assessment["preview_only"] is True
    assert assessment["deterministic"] is True
    assert assessment["non_authoritative"] is True
    assert assessment["non_executing"] is True
    assert assessment["non_approving"] is True
    assert assessment["non_verifying"] is True
    assert len(assessment["rationale"]) <= 160
    assert len(assessment["boundary"]) <= 160
    for field, expected in NO_ACTION_FLAGS.items():
        assert assessment[field] is expected, field


@pytest.mark.parametrize(
    "prompt",
    (
        "Run Maintenance Scan",
        "Maintenance Scan",
        "Bakım Taramasını Çalıştır",
        "Bakım Taraması",
    ),
)
def test_maintenance_scan_assessment_requires_separate_explicit_action(prompt: str) -> None:
    assessment = build_operator_route_preview(prompt)["capability_assessment"]

    assert assessment["classification"] == "observe_only"
    assert "separate explicit user action" in assessment["rationale"]
    assert "no scan has run yet" in assessment["boundary"]
    assert "no authority or execution permission was granted" in assessment["boundary"]
    for field, expected in NO_ACTION_FLAGS.items():
        assert assessment[field] is expected, field


def test_capability_assessment_does_not_mutate_route_metadata() -> None:
    route_preview = {
        "route_id": "safe_plan_builder",
        "primary_intent": "safe_plan",
        "external_cloud_candidate_disabled": False,
    }
    original = deepcopy(route_preview)

    build_capability_assessment("Draft a safe plan", route_preview)

    assert route_preview == original


def test_provider_metadata_never_becomes_readiness() -> None:
    assessment = build_operator_route_preview("Use OpenRouter cloud model")["capability_assessment"]

    assert assessment["classification"] == "provider_unavailable"
    assert "disabled" in assessment["rationale"]
    assert assessment["provider_call_performed"] is False
    assert assessment["execution_authorized"] is False


def test_provider_unavailable_still_precedes_maintenance_scan_wording() -> None:
    assessment = build_operator_route_preview(
        "Run maintenance scan with cloud provider"
    )["capability_assessment"]

    assert assessment["classification"] == "provider_unavailable"
    assert assessment["provider_call_performed"] is False
    assert assessment["execution_authorized"] is False
