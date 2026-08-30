import { app, BrowserWindow, ipcMain, systemPreferences } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import http from 'http';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 340,
    height: 700,
    transparent: true,
    frame: false,
    show: false,
    alwaysOnTop: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  mainWindow.setAlwaysOnTop(true, 'screen-saver', 1);

  mainWindow.loadURL('http://localhost:5180');
}

app.whenReady().then(async () => {
  if (process.platform === 'darwin') {
    const status = systemPreferences.getMediaAccessStatus('microphone');
    if (status !== 'granted') {
      await systemPreferences.askForMediaAccess('microphone');
    }
  }
  createWindow();

  // Local HTTP server to listen for simulate-call triggers
  const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    if (req.method === 'POST' && req.url === '/simulate') {
      let body = '';
      req.on('data', chunk => {
        body += chunk.toString();
      });
      req.on('end', () => {
        try {
          const payload = body ? JSON.parse(body) : {};
          console.log('Received simulate call trigger with session_id:', payload.session_id);
          if (mainWindow) {
            mainWindow.show();
            mainWindow.webContents.send('incoming-call', payload.session_id);
          }
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ status: 'success' }));
        } catch (e) {
          res.writeHead(400);
          res.end();
        }
      });
    } else {
      res.writeHead(404);
      res.end();
    }
  });

  server.listen(3456, '127.0.0.1', () => {
    console.log('Electron local trigger server running on http://127.0.0.1:3456');
  });

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });

  ipcMain.on('hide-window', () => {
    if (mainWindow) {
      mainWindow.hide();
    }
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});
