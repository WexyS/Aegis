"""
Test: AI Parser — Validation, hallucination check, and capability check.
"""

from aegis.intent.ai_parser import AIParser


class TestAIParserValidation:
    
    def setup_method(self) -> None:
        self.ai_parser = AIParser()

    def test_clean_json_markdown(self) -> None:
        raw = "```json\n[{\"intent\": \"type\", \"params\": {\"text\": \"hello\"}}]\n```"
        clean = self.ai_parser._clean_json_response(raw)
        assert clean == "[{\"intent\": \"type\", \"params\": {\"text\": \"hello\"}}]"

    def test_validate_allowed_intents(self) -> None:
        raw_data = [
            {"intent": "type", "params": {"text": "hello"}},
            {"intent": "delete_files", "params": {"path": "C:\\"}} # Should be filtered
        ]
        valid = self.ai_parser._validate_and_filter(raw_data, "test")
        assert len(valid) == 1
        assert valid[0].intent == "type"

    def test_validate_app_capability(self) -> None:
        raw_data = [
            {"intent": "open_app", "params": {"app": "notepad"}},
            {"intent": "open_app", "params": {"app": "unknown_app"}} # Should be filtered
        ]
        valid = self.ai_parser._validate_and_filter(raw_data, "test")
        assert len(valid) == 1
        assert valid[0].params["app"] == "notepad"

    def test_validate_schema_missing_params(self) -> None:
        raw_data = [
            {"intent": "type", "params": {}}, # Missing 'text'
            {"intent": "type", "params": {"text": "valid"}}
        ]
        valid = self.ai_parser._validate_and_filter(raw_data, "test")
        assert len(valid) == 1
        assert valid[0].params["text"] == "valid"

    def test_resolve_risk(self) -> None:
        assert self.ai_parser._resolve_risk("type").value == "medium"
        assert self.ai_parser._resolve_risk("read_file").value == "low"
        assert self.ai_parser._resolve_risk("general_chat").value == "none"
