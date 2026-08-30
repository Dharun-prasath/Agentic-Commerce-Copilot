const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  onIncomingCall: (callback) => ipcRenderer.on('incoming-call', (_event, sessionId) => callback(sessionId)),
  hideWindow: () => ipcRenderer.send('hide-window')
});
