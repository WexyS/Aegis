from __future__ import annotations

from aegis.core.protocol import RuntimeState


VALID_TRANSITIONS: tuple[tuple[tuple[RuntimeState, ...], tuple[RuntimeState, ...]], ...] = (
    ((RuntimeState.IDLE,), (RuntimeState.THINKING,)),
    ((RuntimeState.THINKING,), (RuntimeState.PLANNING, RuntimeState.EXECUTING)),
    ((RuntimeState.PLANNING,), (RuntimeState.EXECUTING,)),
    ((RuntimeState.EXECUTING,), (RuntimeState.VERIFYING, RuntimeState.FAILED)),
    ((RuntimeState.VERIFYING,), (RuntimeState.EXECUTING, RuntimeState.RECOVERING, RuntimeState.COMPLETED)),
    ((RuntimeState.RECOVERING,), (RuntimeState.PLANNING, RuntimeState.EXECUTING, RuntimeState.FAILED)),
    ((RuntimeState.COMPLETED, RuntimeState.FAILED), (RuntimeState.IDLE,)),
    (
        (
            RuntimeState.THINKING,
            RuntimeState.PLANNING,
            RuntimeState.EXECUTING,
            RuntimeState.VERIFYING,
            RuntimeState.RECOVERING,
        ),
        (RuntimeState.IDLE, RuntimeState.FAILED),
    ),
)


def coerce_state(value: RuntimeState | str) -> RuntimeState:
    return value if isinstance(value, RuntimeState) else RuntimeState(value)


def is_valid_transition(from_state: RuntimeState | str, to_state: RuntimeState | str) -> bool:
    source = coerce_state(from_state)
    target = coerce_state(to_state)
    if source == target:
        return True
    return any(source in sources and target in targets for sources, targets in VALID_TRANSITIONS)
