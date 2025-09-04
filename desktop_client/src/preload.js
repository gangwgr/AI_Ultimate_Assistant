const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // App information
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // Store management
  getStoreValue: (key, defaultValue) => ipcRenderer.invoke('get-store-value', key, defaultValue),
  setStoreValue: (key, value) => ipcRenderer.invoke('set-store-value', key, value),
  
  // Dialog management
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  
  // Browser integration
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  
  // Configuration
  resetBackendUrl: () => ipcRenderer.invoke('reset-backend-url'),
  
  // Event listeners
  onNewConversation: (callback) => {
    ipcRenderer.on('new-conversation', callback);
  },
  
  onTriggerVoiceInput: (callback) => {
    ipcRenderer.on('trigger-voice-input', callback);
  },
  
  onShowQuickActions: (callback) => {
    ipcRenderer.on('show-quick-actions', callback);
  },
  
  // Remove listeners
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  },
  
  // Platform information
  platform: process.platform,
  
  // Notification support
  showNotification: (title, body, options = {}) => {
    if (Notification.permission === 'granted') {
      return new Notification(title, { body, ...options });
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          return new Notification(title, { body, ...options });
        }
      });
    }
  }
});

// Expose a safe version of Node.js APIs if needed
contextBridge.exposeInMainWorld('nodeAPI', {
  platform: process.platform,
  versions: process.versions
}); 