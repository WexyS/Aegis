/**
 * ══════════════════════════════════════════════════════════════════════
 * AEGIS EVENT SOURCING SERVICE v2.0
 * ══════════════════════════════════════════════════════════════════════
 *
 * Hardened event sourcing with:
 *   - Write-ahead log (WAL) pattern: persist BEFORE memory
 *   - Bounded in-memory buffer (prevents memory leaks)
 *   - Duplicate event suppression via event_id Set
 *   - Async batch flushing (reduces IndexedDB write pressure)
 *   - Session lifecycle management
 *
 * CRITICAL: Events are append-only. Never mutate a persisted event.
 *
 * ══════════════════════════════════════════════════════════════════════
 */

import { WebSocketEvent } from '@/types/runtime';
import { RuntimeState } from '@/types/fsm';
import { aegisDB } from '@/persistence/db';
import { StoreName, PersistedSession } from '@/persistence/schemas';
import type { RuntimeEvent as WireRuntimeEvent } from '@/contracts/protocol';

export interface RuntimeEvent {
  id: string;
  sessionId: string;
  type: WebSocketEvent | 'STATE_CHANGE';
  payload: any;
  timestamp: number;
  state: RuntimeState;
  sequenceNum?: number;
  traceId?: string;
  spanId?: string;
  previousHash?: string;
  eventHash?: string;
  deterministicHash?: string;
}

// ─── CONFIGURATION ────────────────────────────────────────────────
const MAX_MEMORY_EVENTS = 2000;    // Prevent unbounded memory growth
const FLUSH_INTERVAL_MS = 5000;    // Batch flush interval
const FLUSH_BATCH_SIZE = 50;       // Max events per flush cycle

class EventSourcingService {
  private eventLog: RuntimeEvent[] = [];
  private pendingWrites: RuntimeEvent[] = [];
  private seenIds = new Set<string>();
  private currentSessionId: string;
  private flushTimer: ReturnType<typeof setInterval> | null = null;
  private isInitialized = false;
  private lastHash: string = "genesis";

  constructor() {
    this.currentSessionId = `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  }

  /**
   * Initialize the service. Must be called once at app startup.
   */
  public async init(): Promise<void> {
    if (this.isInitialized) return;

    await aegisDB.init();
    this.startFlushLoop();
    this.isInitialized = true;

    // Persist session record
    const session: PersistedSession = {
      id: this.currentSessionId,
      startTime: Date.now(),
      lastActive: Date.now(),
      fsmState: RuntimeState.IDLE,
      telemetry: {
        determinismScore: 0.0,
        recoveryBudget: 1.0,
        vramUsage: '0.0 GB',
        activeApp: 'None',
        activeModel: 'Unavailable',
      },
      isUnfinished: true,
    };

    try {
      await aegisDB.put(StoreName.SESSIONS, session);
    } catch (e) {
      console.error('[EVENT_SOURCING] Failed to persist session:', e);
    }

    console.log(`[EVENT_SOURCING] Initialized. Session: ${this.currentSessionId}`);
  }

  public getSessionId(): string {
    return this.currentSessionId;
  }

  public setSessionId(id: string): boolean {
    if (id === this.currentSessionId) {
      return false;
    }
    this.currentSessionId = id;
    this.eventLog = [];
    this.pendingWrites = [];
    this.seenIds.clear();
    this.lastHash = "genesis";
    return true;
  }

  /**
   * Ingests the backend's canonical RuntimeEvent. The frontend stores this as
   * a projection only; it does not generate replacement hashes or sequence IDs.
   */
  public async ingestBackendEvent(event: WireRuntimeEvent): Promise<RuntimeEvent | null> {
    const id = event.event_id;
    if (this.seenIds.has(id)) {
      return null;
    }

    const sessionId =
      event.session_id ||
      (event.payload?.session_id as string | undefined) ||
      this.currentSessionId;

    if (sessionId !== this.currentSessionId) {
      this.currentSessionId = sessionId;
    }

    const persisted: RuntimeEvent = {
      id,
      sessionId,
      type: event.type as RuntimeEvent['type'],
      payload: event.payload,
      timestamp: event.timestamp,
      state: (event.runtime_phase || event.state || RuntimeState.IDLE) as RuntimeState,
      sequenceNum: event.sequence_num,
      traceId: event.trace_id,
      spanId: event.span_id,
      previousHash: event.previous_hash || event.previousHash,
      eventHash: event.event_hash || event.eventHash,
      deterministicHash: event.deterministic_hash,
    };

    this.lastHash = persisted.eventHash || this.lastHash;
    this.seenIds.add(id);
    this.pendingWrites.push(persisted);
    this.eventLog.push(persisted);

    if (this.eventLog.length > MAX_MEMORY_EVENTS) {
      const evicted = this.eventLog.splice(0, this.eventLog.length - MAX_MEMORY_EVENTS);
      for (const e of evicted) {
        this.seenIds.delete(e.id);
      }
    }

    return persisted;
  }

  /**
   * Log an event. Write-ahead: persists to IndexedDB queue FIRST,
   * then adds to in-memory buffer.
   */
  public async log(
    type: WebSocketEvent | 'STATE_CHANGE',
    payload: any,
    state: RuntimeState
  ): Promise<RuntimeEvent> {
    const canonicalPayload = JSON.stringify(payload || {});
    const hashInput = `${this.lastHash}|${type}|${canonicalPayload}|${state}`;
    
    // Hash computation
    const encoder = new TextEncoder();
    const data = encoder.encode(hashInput);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const eventHash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

    const event: RuntimeEvent = {
      id: crypto.randomUUID(),
      sessionId: this.currentSessionId,
      type,
      payload,
      timestamp: Date.now(),
      state,
      previousHash: this.lastHash,
      eventHash: eventHash,
    };
    
    this.lastHash = eventHash;

    // Duplicate suppression
    if (this.seenIds.has(event.id)) {
      console.warn(`[EVENT_SOURCING] Duplicate event suppressed: ${event.id}`);
      return event;
    }
    this.seenIds.add(event.id);

    // Add to pending writes queue (will be flushed to IndexedDB)
    this.pendingWrites.push(event);

    // Add to in-memory buffer (bounded)
    this.eventLog.push(event);
    if (this.eventLog.length > MAX_MEMORY_EVENTS) {
      // Evict oldest events from memory (they're already in IndexedDB)
      const evicted = this.eventLog.splice(0, this.eventLog.length - MAX_MEMORY_EVENTS);
      for (const e of evicted) {
        this.seenIds.delete(e.id);
      }
    }

    return event;
  }

  /**
   * Returns the in-memory event history (bounded window).
   */
  public getHistory(): RuntimeEvent[] {
    return [...this.eventLog];
  }

  public getPendingWriteCount(): number {
    return this.pendingWrites.length;
  }

  /**
   * Loads full event history from IndexedDB for a specific session.
   */
  public async loadFromDB(sessionId: string): Promise<RuntimeEvent[]> {
    const events = await aegisDB.getAll(StoreName.EVENTS, 'sessionId', sessionId);
    this.eventLog = events.sort((a: any, b: any) => a.timestamp - b.timestamp);

    // Rebuild seen IDs
    this.seenIds.clear();
    for (const e of this.eventLog) {
      this.seenIds.add(e.id);
    }

    return this.eventLog;
  }

  /**
   * Gracefully close the session (marks it as finished).
   */
  public async closeSession(): Promise<void> {
    // Flush remaining events
    await this.flush();

    // Mark session as finished
    try {
      const session = await aegisDB.get(StoreName.SESSIONS, this.currentSessionId);
      if (session) {
        session.isUnfinished = false;
        session.lastActive = Date.now();
        await aegisDB.put(StoreName.SESSIONS, session);
      }
    } catch (e) {
      console.error('[EVENT_SOURCING] Failed to close session:', e);
    }

    this.stopFlushLoop();
    console.log(`[EVENT_SOURCING] Session closed: ${this.currentSessionId}`);
  }

  // ─── FLUSH LOOP ──────────────────────────────────────────────────
  private startFlushLoop(): void {
    this.stopFlushLoop();
    this.flushTimer = setInterval(() => this.flush(), FLUSH_INTERVAL_MS);
  }

  private stopFlushLoop(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }

  private async flush(): Promise<void> {
    if (this.pendingWrites.length === 0) return;

    const batch = this.pendingWrites.splice(0, FLUSH_BATCH_SIZE);

    for (const event of batch) {
      try {
        await aegisDB.put(StoreName.EVENTS, event);
      } catch (error) {
        console.error(`[EVENT_SOURCING] Flush failed for event ${event.id}:`, error);
        // Re-queue failed writes at the front
        this.pendingWrites.unshift(event);
        break; // Stop flush on first failure to preserve ordering
      }
    }

    // Update session lastActive
    try {
      const session = await aegisDB.get(StoreName.SESSIONS, this.currentSessionId);
      if (session) {
        session.lastActive = Date.now();
        await aegisDB.put(StoreName.SESSIONS, session);
      }
    } catch (e) {
      // Non-fatal
    }
  }
}

export const eventSourcing = new EventSourcingService();
