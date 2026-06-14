const { app, BrowserWindow, ipcMain, session } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
const WINDOW_ACTION_CHANNEL = 'aegis:window-action';
const WINDOW_ACTIONS = new Set(['minimize', 'toggle-maximize', 'toggle-fullscreen', 'close']);

const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    const mainWindow = BrowserWindow.getAllWindows()[0];
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  function createWindow() {
    session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
      callback({
        responseHeaders: {
          ...details.responseHeaders,
          'Content-Security-Policy': ["default-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:* ws://localhost:* http://127.0.0.1:* ws://127.0.0.1:* data:;"]
        }
      });
    });

    const win = new BrowserWindow({
      width: 1400,
      height: 900,
      minWidth: 1180,
      minHeight: 760,
      frame: false,
      fullscreenable: true,
      maximizable: true,
      minimizable: true,
      autoHideMenuBar: true,
      show: false,
      backgroundColor: '#030712',
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        sandbox: true,
        preload: path.join(__dirname, 'preload.js'),
      },
    });

    win.once('ready-to-show', () => {
      win.maximize();
      win.show();
      win.focus();
    });

    win.webContents.on('crashed', (e) => {
      console.error('Renderer process crashed! Restarting...');
      win.reload();
    });

    win.webContents.on('before-input-event', (event, input) => {
      if (input.type === 'keyDown' && input.key === 'F11') {
        win.setFullScreen(!win.isFullScreen());
        event.preventDefault();
      }
    });

    const url = isDev 
      ? 'http://localhost:3000' 
      : `file://${path.join(__dirname, '../out/index.html')}`;

    win.loadURL(url);

    if (isDev && process.env.AEGIS_OPEN_DEVTOOLS === '1') {
      win.webContents.openDevTools({ mode: 'detach' });
    }
  }

  ipcMain.on(WINDOW_ACTION_CHANNEL, (event, action) => {
    if (!WINDOW_ACTIONS.has(action)) return;
    const win = BrowserWindow.fromWebContents(event.sender);
    if (!win) return;

    if (action === 'minimize') {
      win.minimize();
      return;
    }

    if (action === 'toggle-maximize') {
      if (win.isMaximized()) {
        win.unmaximize();
      } else {
        win.maximize();
      }
      return;
    }

    if (action === 'toggle-fullscreen') {
      win.setFullScreen(!win.isFullScreen());
      return;
    }

    if (action === 'close') {
      win.close();
    }
  });

  app.whenReady().then(createWindow);

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
}
