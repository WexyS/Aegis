// src/persistence/schemas.ts

import { RuntimeState } from '@/types/fsm';
import { RuntimeStep, TelemetryData, WebSocketEvent } from '@/types/runtime';

export const DB_NAME = 'AegisRuntimeDB';
export const DB_VERSION = 2;

export enum StoreName {
  SESSIONS = 'sessions',
  MESSAGES = 'messages',
  EVENTS = 'events',
  SNAPSHOTS = 'snapshots',
}

export interface PersistedSession {
  id: string;
  startTime: number;
  lastActive: number;
  fsmState: RuntimeState;
  telemetry: TelemetryData;
  isUnfinished: boolean;
}

export interface PersistedEvent {
  id: string;
  sessionId: string;
  type: WebSocketEvent | 'STATE_CHANGE';
  payload: any;
  timestamp: number;
  state: RuntimeState;
  previousHash?: string;
  eventHash?: string;
}

export interface RuntimeSnapshot {
  id: string;
  sessionId: string;
  timestamp: number;
  fsmState: RuntimeState;
  steps: RuntimeStep[];
  chatHistory: any[];
}
