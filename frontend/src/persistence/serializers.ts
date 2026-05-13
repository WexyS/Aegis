// src/persistence/serializers.ts

import { RuntimeStoreState } from '@/store/useRuntimeStore';
import { ChatState } from '@/store/useChatStore';
import { RuntimeSnapshot } from './schemas';

export class RuntimeSerializer {
  /**
   * Serializes the entire runtime state into a replay-safe, normalized snapshot.
   */
  public static serialize(
    sessionId: string, 
    runtime: any, 
    chat: any
  ): RuntimeSnapshot {
    return {
      id: crypto.randomUUID(),
      sessionId,
      timestamp: Date.now(),
      fsmState: runtime.currentState,
      steps: [...runtime.steps],
      chatHistory: [...chat.messages],
    };
  }

  /**
   * Hydrates the stores from a persisted snapshot.
   */
  public static hydrate(snapshot: RuntimeSnapshot, runtimeStore: any, chatStore: any) {
    console.log(`[SNAPSHOT] Hydrating Runtime from Snapshot: ${snapshot.timestamp}`);
    
    runtimeStore.transitionTo(snapshot.fsmState, { isHydration: true });
    // Note: We don't use addStep here to avoid duplication; we replace the timeline.
    runtimeStore.setTelemetry({
      steps: snapshot.steps,
    });
    
    // Chat hydration
    snapshot.chatHistory.forEach(msg => chatStore.addMessage(msg));
  }
}
