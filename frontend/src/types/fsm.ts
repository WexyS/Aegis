// src/types/fsm.ts

export enum RuntimeState {
  IDLE = 'IDLE',
  THINKING = 'THINKING',
  PLANNING = 'PLANNING',
  EXECUTING = 'EXECUTING',
  VERIFYING = 'VERIFYING',
  RECOVERING = 'RECOVERING',
  FAILED = 'FAILED',
  COMPLETED = 'COMPLETED',
}

export type StateTransition = {
  from: RuntimeState | RuntimeState[];
  to: RuntimeState | RuntimeState[];
};

export const VALID_TRANSITIONS: StateTransition[] = [
  // Standard pipeline
  { from: RuntimeState.IDLE, to: RuntimeState.THINKING },
  { from: RuntimeState.THINKING, to: RuntimeState.PLANNING },
  { from: RuntimeState.THINKING, to: RuntimeState.EXECUTING }, // Direct tool call (no plan step)
  { from: RuntimeState.PLANNING, to: RuntimeState.EXECUTING },
  { from: RuntimeState.EXECUTING, to: RuntimeState.VERIFYING },
  { from: RuntimeState.EXECUTING, to: RuntimeState.FAILED },   // Immediate failure
  { from: RuntimeState.VERIFYING, to: [RuntimeState.EXECUTING, RuntimeState.RECOVERING, RuntimeState.COMPLETED] },
  { from: RuntimeState.RECOVERING, to: [RuntimeState.PLANNING, RuntimeState.EXECUTING, RuntimeState.FAILED] },

  // Terminal → reset
  { from: [RuntimeState.COMPLETED, RuntimeState.FAILED], to: RuntimeState.IDLE },

  // Emergency reset: any state can return to IDLE or FAILED (e.g. user abort, crash recovery, parsing error)
  { from: [RuntimeState.THINKING, RuntimeState.PLANNING, RuntimeState.EXECUTING, RuntimeState.VERIFYING, RuntimeState.RECOVERING], to: [RuntimeState.IDLE, RuntimeState.FAILED] },
];

