"""
AEGIS — Local-first, verification-backed desktop automation runtime.

Top-level package organization:
  - core:         Runtime authority, schemas, protocol, journal, audit
  - api:          FastAPI routes and Socket.IO runtime bridge
  - orchestrator: Command pipeline coordinator and completion gate
  - intent:       Deterministic intent parsing with controlled model fallback
  - guard:        Risk, approval, and policy evaluation
  - executor:     Controlled execution and evidence collection
  - replay:       Journal-backed replay and projection utilities
  - tools:        Bounded tool implementations and canonical registry
  - logger:       Structured logging and audit support

Memory, RAG, voice, and vision should remain bounded future layers until their
runtime contracts are evidence-backed and approval-aware.
"""

__version__ = "0.1.0"
__app_name__ = "Aegis"
