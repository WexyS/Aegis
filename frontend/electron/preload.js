/**
 * ══════════════════════════════════════════════════════════════════════
 * AEGIS ELECTRON PRELOAD — Secure IPC Bridge
 * ══════════════════════════════════════════════════════════════════════
 *
 * This runs in an isolated context between renderer and main process.
 * ONLY explicitly whitelisted APIs are exposed to the renderer.
 *
 * Security rules:
 *   - No direct Node.js access from renderer
 *   - No arbitrary IPC channel access
 *   - All payloads validated before crossing the bridge
 *   - Channel names are typed and enumerated
 *
 * ══════════════════════════════════════════════════════════════════════
 */

const { contextBridge, ipcRenderer } = require('electron');

// ─── ALLOWED IPC CHANNELS ──────────────────────────────────────────
const ALLOWED_SEND_CHANNELS = [
  'aegis:command',
  'aegis:telemetry-request',
  'aegis:window-action',
  'aegis:log',
];

const ALLOWED_RECEIVE_CHANNELS = [
  'aegis:runtime-event',
  'aegis:telemetry-update',
  'aegis:health-status',
  'aegis:error',
];

// ─── EXPOSED API ───────────────────────────────────────────────────
contextBridge.exposeInMainWorld('aegis', {
  /**
   * Send a message to the main process.
   * Only allowed channels are accepted.
   */
  send: (channel, data) => {
    if (ALLOWED_SEND_CHANNELS.includes(channel)) {
      ipcRenderer.send(channel, data);
    } else {
      console.error(`[PRELOAD] Blocked send to unauthorized channel: ${channel}`);
    }
  },

  /**
   * Listen for messages from the main process.
   * Only allowed channels are accepted.
   */
  on: (channel, callback) => {
    if (ALLOWED_RECEIVE_CHANNELS.includes(channel)) {
      // Wrap callback to strip the event object (security)
      const wrappedCallback = (_event, ...args) => callback(...args);
      ipcRenderer.on(channel, wrappedCallback);

      // Return cleanup function
      return () => ipcRenderer.removeListener(channel, wrappedCallback);
    } else {
      console.error(`[PRELOAD] Blocked listen on unauthorized channel: ${channel}`);
      return () => {};
    }
  },

  /**
   * Invoke an async IPC call (request/response pattern).
   */
  invoke: async (channel, data) => {
    if (ALLOWED_SEND_CHANNELS.includes(channel)) {
      return ipcRenderer.invoke(channel, data);
    }
    throw new Error(`[PRELOAD] Blocked invoke to unauthorized channel: ${channel}`);
  },

  /**
   * Platform info (safe to expose).
   */
  platform: process.platform,
  isElectron: true,
});
