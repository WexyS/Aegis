from __future__ import annotations

from aegis.tools.registry import (
    get_tool_registry_snapshot,
    get_tool_spec,
    list_tools,
    validate_registry_drift,
)


def test_tool_registry_contract_has_no_config_drift() -> None:
    drift = validate_registry_drift()

    assert drift["status"] == "ok"
    assert drift["missing_in_config"] == []
    assert drift["missing_in_code"] == []
    assert drift["missing_specs"] == []
    assert drift["mismatches"] == []


def test_tool_registry_snapshot_is_backend_source_of_truth() -> None:
    snapshot = get_tool_registry_snapshot()

    assert snapshot["scan_version"] == "tool-registry/1"
    assert snapshot["read_only"] is True
    assert snapshot["status"] == "ok"
    assert snapshot["registered_count"] == len(list_tools())
    assert any(tool["name"] == "run_command" for tool in snapshot["tools"])
    assert any(tool["name"] == "list_directory" for tool in snapshot["tools"])


def test_tool_specs_capture_risk_approval_and_evidence_policy() -> None:
    read_spec = get_tool_spec("read_file")
    edit_spec = get_tool_spec("edit_file")
    delete_spec = get_tool_spec("delete_file")
    shell_spec = get_tool_spec("run_command")

    assert read_spec is not None and read_spec.risk_level.value == "low"
    assert edit_spec is not None and edit_spec.requires_approval is True
    assert edit_spec.evidence_policy == "file_diff"
    assert delete_spec is not None and delete_spec.risk_level.value == "critical"
    assert shell_spec is not None and shell_spec.cancellation_supported is True
