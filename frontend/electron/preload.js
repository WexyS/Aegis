const { contextBridge, ipcRenderer } = require('electron');

const ALLOWED_SEND_CHANNELS = new Set([
  'aegis:command',
  'aegis:telemetry-request',
  'aegis:window-action',
  'aegis:log',
]);

const ALLOWED_RECEIVE_CHANNELS = new Set([
  'aegis:runtime-event',
  'aegis:telemetry-update',
  'aegis:health-status',
  'aegis:error',
]);

const ALLOWED_WINDOW_ACTIONS = new Set([
  'minimize',
  'toggle-maximize',
  'toggle-fullscreen',
  'close',
]);

function sendAllowed(channel, data) {
  if (!ALLOWED_SEND_CHANNELS.has(channel)) {
    console.error(`[PRELOAD] Blocked send to unauthorized channel: ${channel}`);
    return;
  }
  ipcRenderer.send(channel, data);
}

contextBridge.exposeInMainWorld('aegis', {
  send: sendAllowed,

  on: (channel, callback) => {
    if (!ALLOWED_RECEIVE_CHANNELS.has(channel)) {
      console.error(`[PRELOAD] Blocked listen on unauthorized channel: ${channel}`);
      return () => {};
    }

    const wrappedCallback = (_event, ...args) => callback(...args);
    ipcRenderer.on(channel, wrappedCallback);
    return () => ipcRenderer.removeListener(channel, wrappedCallback);
  },

  invoke: async (channel, data) => {
    if (!ALLOWED_SEND_CHANNELS.has(channel)) {
      throw new Error(`[PRELOAD] Blocked invoke to unauthorized channel: ${channel}`);
    }
    return ipcRenderer.invoke(channel, data);
  },

  windowAction: (action) => {
    if (!ALLOWED_WINDOW_ACTIONS.has(action)) {
      console.error(`[PRELOAD] Blocked unauthorized window action: ${action}`);
      return;
    }
    sendAllowed('aegis:window-action', action);
  },

  platform: process.platform,
  isElectron: true,
});
