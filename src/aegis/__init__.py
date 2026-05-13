"""
AEGIS — Local-first, multi-modal, secure desktop AI copilot.

This is the top-level package. All submodules are organized by responsibility:
  - core:         Deterministic core (schemas, config, errors, constants)
  - api:          FastAPI HTTP routers
  - orchestrator: Central pipeline coordinator
  - intent:       Intent parsing (rule-based + model fallback)
  - guard:        Action guard (security backbone)
  - executor:     Controlled execution (dry-run default)
  - memory:       Multi-layer memory stack
  - rag:          RAG / knowledge layer
  - models:       Model router (local-first)
  - tools:        Tool system (schema-driven, auditable)
  - logger:       Structured logging, audit, replay
"""

__version__ = "0.1.0"
__app_name__ = "Aegis"
