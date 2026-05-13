// src/persistence/recovery.ts

import { aegisDB } from './db';
import { StoreName, PersistedSession } from './schemas';
import { RuntimeState } from '@/types/fsm';

export class RecoveryEngine {
  /**
   * Scans for sessions that were interrupted during active execution.
   */
  public async detectInterruptedSession(): Promise<PersistedSession | null> {
    try {
      const sessions = (await aegisDB.getAll(StoreName.SESSIONS)) as PersistedSession[];
      
      // Look for sessions where state was active and not gracefully closed
      const interrupted = sessions
        .filter(s => s.isUnfinished)
        .sort((a, b) => b.lastActive - a.lastActive)[0];

      if (interrupted && this.isStateCritical(interrupted.fsmState)) {
        return interrupted;
      }
      return null;
    } catch (error) {
      console.error('[RECOVERY] Detection failed:', error);
      return null;
    }
  }

  private isStateCritical(state: RuntimeState): boolean {
    const criticalStates = [
      RuntimeState.EXECUTING,
      RuntimeState.PLANNING,
      RuntimeState.VERIFYING,
      RuntimeState.RECOVERING,
      RuntimeState.THINKING
    ];
    return criticalStates.includes(state);
  }

  /**
   * Reconstructs the runtime state from the event journal.
   */
  public async bootFromJournal(sessionId: string) {
    console.log(`[RECOVERY] Reconstructing Session: ${sessionId}`);
    
    const events = await aegisDB.getAll(StoreName.EVENTS, 'sessionId', sessionId);
    const sortedEvents = events.sort((a, b) => a.timestamp - b.timestamp);
    
    return {
      eventCount: sortedEvents.length,
      lastState: sortedEvents[sortedEvents.length - 1]?.state || RuntimeState.IDLE,
      journal: sortedEvents
    };
  }
}

export const recoveryEngine = new RecoveryEngine();
