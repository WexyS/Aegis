export {};

type AegisWindowAction = 'minimize' | 'toggle-maximize' | 'toggle-fullscreen' | 'close';

declare global {
  interface Window {
    aegis?: {
      send?: (channel: string, data?: unknown) => void;
      on?: (channel: string, callback: (...args: unknown[]) => void) => () => void;
      invoke?: (channel: string, data?: unknown) => Promise<unknown>;
      windowAction?: (action: AegisWindowAction) => void;
      platform?: string;
      isElectron?: boolean;
    };
  }
}
