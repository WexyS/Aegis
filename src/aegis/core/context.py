# src/aegis/core/context.py

from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class ExecutionContext:
    """
    AEGIS Execution Context.
    The primary carrier for traceability data (Traces and Spans).
    Passed across Orchestrator, Executor, and Tools.
    """
    trace_id: UUID
    span_id: UUID
    parent_span_id: Optional[UUID] = None
    step_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_root(cls) -> "ExecutionContext":
        """Initializes a new trace with a root span."""
        return cls(
            trace_id=uuid4(),
            span_id=uuid4(),
            parent_span_id=None,
            step_index=0
        )

    def create_child(self, step_index: Optional[int] = None) -> "ExecutionContext":
        """Creates a new span within the same trace."""
        return ExecutionContext(
            trace_id=self.trace_id,
            span_id=uuid4(),
            parent_span_id=self.span_id,
            step_index=step_index if step_index is not None else self.step_index,
            metadata=self.metadata.copy()
        )

    def with_step(self, index: int) -> "ExecutionContext":
        """Returns a copy of the context for a specific step index."""
        return ExecutionContext(
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_span_id=self.parent_span_id,
            step_index=index,
            metadata=self.metadata.copy()
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": str(self.trace_id),
            "span_id": str(self.span_id),
            "parent_span_id": str(self.parent_span_id) if self.parent_span_id else None,
            "step_index": self.step_index
        }
