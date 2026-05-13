/**
 * ══════════════════════════════════════════════════════════════════════
 * AEGIS REPLAY VALIDATION ENGINE
 * ══════════════════════════════════════════════════════════════════════
 *
 * Frontend-side replay engine. Reconstructs runtime state purely from
 * persisted events — NO side effects, NO tool execution, NO OS calls.
 *
 * Provides:
 *   - Deterministic state reconstruction
 *   - Divergence detection (expected vs actual)
 *   - Integrity checksum (SHA-256 chain hash)
 *   - Replay profiling
 *   - Sandbox mode (isolated from live stores)
 *
 * ══════════════════════════════════════════════════════════════════════
 */

import { RuntimeState, VALID_TRANSITIONS } from '@/types/fsm';
import { RuntimeEvent } from '@/contracts/protocol';
import { aegisDB } from '@/persistence/db';
import { StoreName } from '@/persistence/schemas';

// ─── REPLAY STATE ──────────────────────────────────────────────────
export interface ReplaySnapshot {
  fsmState: RuntimeState;
  eventIndex: number;
  timestamp: number;
  stepCount: number;
  determinismScore: number;
  recoveryDepth: number;
}

export interface ReplayDivergence {
  eventIndex: number;
  field: string;
  expected: unknown;
  actual: unknown;
  severity: 'warning' | 'critical';
}

export interface ReplayResult {
  success: boolean;
  totalEvents: number;
  processedEvents: number;
  finalState: ReplaySnapshot;
  divergences: ReplayDivergence[];
  integrityHash: string;
  durationMs: number;
  consistencyScore: number; // 0.0 - 1.0
  integrityScore: number;
  corruptionIndex: number;
  divergenceConfidence: number;
}

// ─── FSM TRANSITION VALIDATOR ──────────────────────────────────────
function isValidTransition(from: RuntimeState, to: RuntimeState): boolean {
  if (from === to) return true;
  return VALID_TRANSITIONS.some(t => {
    const fromMatch = Array.isArray(t.from) ? t.from.includes(from) : t.from === from;
    const toMatch = Array.isArray(t.to) ? t.to.includes(to) : t.to === to;
    return fromMatch && toMatch;
  });
}

async function computeEventHash(event: RuntimeEvent, previousHash: string): Promise<string> {
  const canonicalPayload = JSON.stringify(event.payload || {});
  const hashInput = `${previousHash}|${event.type}|${canonicalPayload}|${event.state}`;
  
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    const encoder = new TextEncoder();
    const data = encoder.encode(hashInput);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }
  
  let hash = 0;
  for (let i = 0; i < hashInput.length; i++) {
    const char = hashInput.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return Math.abs(hash).toString(16).padStart(8, '0');
}

// ─── REPLAY-SAFE REDUCER ──────────────────────────────────────────
// Pure function: takes current state + event -> next state. No side effects.
function replayReduce(
  state: ReplaySnapshot,
  event: RuntimeEvent,
  index: number
): { nextState: ReplaySnapshot; divergence: ReplayDivergence | null } {
  const payload = event.payload as Record<string, unknown>;
  let divergence: ReplayDivergence | null = null;

  const nextState: ReplaySnapshot = { ...state, eventIndex: index, timestamp: event.timestamp };

  switch (event.type) {
    case 'STATE_CHANGE': {
      const to = payload.to as RuntimeState;
      const from = payload.from as RuntimeState;

      // Validate FSM transition legality
      if (from && from !== state.fsmState) {
        divergence = {
          eventIndex: index,
          field: 'fsmState',
          expected: from,
          actual: state.fsmState,
          severity: 'critical',
        };
      }

      if (to && !isValidTransition(state.fsmState, to)) {
        divergence = {
          eventIndex: index,
          field: 'fsmTransition',
          expected: `valid transition from ${state.fsmState}`,
          actual: `${state.fsmState} -> ${to}`,
          severity: 'critical',
        };
      }

      if (to) {
        nextState.fsmState = to;
      }

      // Reset recovery on completion/idle
      if (to === RuntimeState.COMPLETED || to === RuntimeState.IDLE) {
        nextState.recoveryDepth = 0;
      }
      break;
    }

    case 'ACTION_STARTED': {
      nextState.stepCount += 1;
      break;
    }

    case 'ACTION_COMPLETED': {
      const success = payload.success as boolean | undefined;
      if (success !== undefined) {
        // Running average determinism
        nextState.determinismScore = (state.determinismScore * state.stepCount + (success ? 1.0 : 0.0)) / (state.stepCount + 1);
      }
      break;
    }

    case 'RECOVERY_TRIGGERED': {
      nextState.recoveryDepth += 1;
      if (nextState.recoveryDepth > 5) {
        divergence = {
          eventIndex: index,
          field: 'recoveryDepth',
          expected: '<= 5',
          actual: nextState.recoveryDepth,
          severity: 'critical',
        };
      }
      break;
    }

    case 'TELEMETRY_UPDATE': {
      const score = payload.determinism_score as number | undefined;
      if (score !== undefined) {
        nextState.determinismScore = score;
      }
      break;
    }

    default:
      // Events that don't affect state are pass-through
      break;
  }

  return { nextState, divergence };
}

// ═══════════════════════════════════════════════════════════════════
// PUBLIC API
// ═══════════════════════════════════════════════════════════════════

export class ReplayEngine {
  /**
   * Replays a session from persisted events.
   * Pure computation — no OS interaction, no store mutation.
   */
  async replaySession(sessionId: string): Promise<ReplayResult> {
    const startTime = performance.now();

    // 1. Load events from IndexedDB
    const rawEvents = await aegisDB.getAll(StoreName.EVENTS, 'sessionId', sessionId);
    const events = rawEvents
      .sort((a: any, b: any) => a.timestamp - b.timestamp) as RuntimeEvent[];

    if (events.length === 0) {
      return {
        success: false,
        totalEvents: 0,
        processedEvents: 0,
        finalState: this.initialState(),
        divergences: [],
        integrityHash: '',
        durationMs: performance.now() - startTime,
        consistencyScore: 0,
        integrityScore: 0,
        corruptionIndex: 0,
        divergenceConfidence: 1.0,
      };
    }

    // 2. Cryptographic Chain Verification
    let runningHash = "genesis";
    const divergences: ReplayDivergence[] = [];
    let isChainValid = true;

    for (let i = 0; i < events.length; i++) {
      const event = events[i];

      // Missing/Tampered link detection
      if (event.previousHash && event.previousHash !== runningHash) {
        divergences.push({
          eventIndex: i,
          field: 'previousHash',
          expected: runningHash,
          actual: event.previousHash,
          severity: 'critical'
        });
        isChainValid = false;
        break; // Fail Closed on cryptographic mismatch
      }

      const expectedEventHash = await computeEventHash(event, runningHash);
      if (event.eventHash && event.eventHash !== expectedEventHash) {
        divergences.push({
          eventIndex: i,
          field: 'eventHash',
          expected: expectedEventHash,
          actual: event.eventHash,
          severity: 'critical'
        });
        isChainValid = false;
        break; // Fail Closed
      }

      runningHash = event.eventHash || expectedEventHash;
    }

    if (!isChainValid) {
      console.error("[REPLAY] FATAL: Cryptographic chain validation failed. Replay aborted.");
      return {
        success: false,
        totalEvents: events.length,
        processedEvents: 0,
        finalState: this.initialState(),
        divergences,
        integrityHash: 'CORRUPTED',
        durationMs: performance.now() - startTime,
        consistencyScore: 0,
        integrityScore: 0,
        corruptionIndex: divergences.length,
        divergenceConfidence: 1.0,
      };
    }

    // 3. Replay through reducer
    let state = this.initialState();
    let processed = 0;

    for (let i = 0; i < events.length; i++) {
      const event = events[i];

      // Event ordering check
      if (i > 0 && event.timestamp < events[i - 1].timestamp) {
        divergences.push({
          eventIndex: i,
          field: 'timestamp',
          expected: `>= ${events[i - 1].timestamp}`,
          actual: event.timestamp,
          severity: 'warning',
        });
      }

      const { nextState, divergence } = replayReduce(state, event, i);
      state = nextState;
      if (divergence) {
        divergences.push(divergence);
        if (divergence.severity === 'critical') {
          // FSM Violation - fail closed
          console.error(`[REPLAY] FATAL: FSM Violation at event ${i}. Replay aborted.`);
          break;
        }
      }
      processed++;
    }

    // 4. Compute consistency score
    const criticalCount = divergences.filter(d => d.severity === 'critical').length;
    const consistencyScore = Math.max(0, 1.0 - (criticalCount * 0.2) - (divergences.length * 0.02));
    const integrityScore = isChainValid ? 1.0 : 0.0;
    const corruptionIndex = criticalCount;
    const divergenceConfidence = processed / events.length;

    return {
      success: criticalCount === 0 && isChainValid,
      totalEvents: events.length,
      processedEvents: processed,
      finalState: state,
      divergences,
      integrityHash: runningHash,
      durationMs: performance.now() - startTime,
      consistencyScore,
      integrityScore,
      corruptionIndex,
      divergenceConfidence,
    };
  }

  /**
   * Validates that a stored hash matches the current event chain.
   */
  async validateIntegrity(sessionId: string, expectedHash: string): Promise<boolean> {
    const result = await this.replaySession(sessionId);
    return result.integrityHash === expectedHash && result.integrityScore === 1.0;
  }

  private initialState(): ReplaySnapshot {
    return {
      fsmState: RuntimeState.IDLE,
      eventIndex: -1,
      timestamp: 0,
      stepCount: 0,
      determinismScore: 1.0,
      recoveryDepth: 0,
    };
  }
}

export const replayEngine = new ReplayEngine();
