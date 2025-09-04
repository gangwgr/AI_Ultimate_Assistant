const { app, BrowserWindow, Menu, shell, ipcMain, dialog, Tray, nativeImage } = require('electron');
const path = require('path');
const Store = require('electron-store');
const windowStateKeeper = require('electron-window-state');
const contextMenu = require('electron-context-menu');
const AutoLaunch = require('auto-launch');
const { autoUpdater } = require('electron-updater');

// Initialize store for user preferences
const store = new Store();

// Keep a global reference of the window object
let mainWindow;
let tray = null;
let isQuitting = false;

// Auto-launch setup
const autoLauncher = new AutoLaunch({
  name: 'AI Ultimate Assistant',
  path: app.getPath('exe'),
});

// Function to request microphone permission explicitly
async function requestMicrophonePermission() {
  try {
    const { systemPreferences } = require('electron');
    
    if (process.platform === 'darwin') {
      const microphoneStatus = systemPreferences.getMediaAccessStatus('microphone');
      console.log('Current microphone status:', microphoneStatus);
      
      if (microphoneStatus === 'not-determined') {
        console.log('Requesting microphone access...');
        const granted = await systemPreferences.askForMediaAccess('microphone');
        console.log('Microphone access granted:', granted);
        return granted;
      } else if (microphoneStatus === 'granted') {
        console.log('Microphone access already granted');
        return true;
      } else {
        console.log('Microphone access denied or restricted');
        return false;
      }
    }
    return true; // Non-macOS platforms
  } catch (error) {
    console.error('Error requesting microphone permission:', error);
    return false;
  }
}

// Enable command line arguments for voice recognition
app.commandLine.appendSwitch('enable-features', 'MediaDevices,WebSpeechAPI');
app.commandLine.appendSwitch('enable-web-speech-api');
app.commandLine.appendSwitch('allow-insecure-localhost');
app.commandLine.appendSwitch('disable-web-security');
app.commandLine.appendSwitch('enable-experimental-web-platform-features');
app.commandLine.appendSwitch('ignore-certificate-errors');
app.commandLine.appendSwitch('ignore-ssl-errors');
app.commandLine.appendSwitch('ignore-certificate-errors-spki-list');
app.commandLine.appendSwitch('disable-features', 'VizDisplayCompositor');

// Enable live reload for development
if (process.env.NODE_ENV === 'development') {
  try {
    require('electron-reload')(__dirname, {
      electron: path.join(__dirname, '..', 'node_modules', '.bin', 'electron'),
      hardResetMethod: 'exit'
    });
  } catch (e) {
    console.log('Electron reload not available in production');
  }
}

// Certificate error handling not needed for HTTP connections

function createWindow() {
  // Load the previous window state or set defaults
  let mainWindowState = windowStateKeeper({
    defaultWidth: 1200,
    defaultHeight: 800
  });

  // Create the browser window
  mainWindow = new BrowserWindow({
    x: mainWindowState.x,
    y: mainWindowState.y,
    width: mainWindowState.width,
    height: mainWindowState.height,
    minWidth: 800,
    minHeight: 600,
    icon: path.join(__dirname, '../assets/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false, // Disable for localhost development and voice recognition
      allowRunningInsecureContent: true,
      experimentalFeatures: true
    },
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    show: false, // Don't show until ready
    autoHideMenuBar: store.get('autoHideMenuBar', false)
  });

  // Let windowStateKeeper manage the window
  mainWindowState.manage(mainWindow);

  // Load the application
  const backendUrl = store.get('backendUrl', 'http://localhost:8000');
  mainWindow.loadFile(path.join(__dirname, 'renderer/index.html'), {
    query: { backend: backendUrl }
  });

  // Handle permissions for microphone access
  mainWindow.webContents.session.setPermissionRequestHandler((webContents, permission, callback) => {
    const allowedPermissions = ['microphone', 'camera', 'notifications', 'media'];
    
    if (allowedPermissions.includes(permission)) {
      callback(true); // Allow microphone and camera access
    } else {
      callback(false);
    }
  });

  // Handle permissions check
  mainWindow.webContents.session.setPermissionCheckHandler((webContents, permission, requestingOrigin) => {
    const allowedPermissions = ['microphone', 'camera', 'notifications', 'media'];
    return allowedPermissions.includes(permission);
  });

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Focus window on creation
    if (process.platform === 'darwin') {
      mainWindow.focus();
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle minimize to tray
  mainWindow.on('minimize', (event) => {
    if (store.get('minimizeToTray', true)) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  // Handle close to tray
  mainWindow.on('close', (event) => {
    if (!isQuitting && store.get('closeToTray', true)) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Handle navigation
  mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);
    
    if (parsedUrl.origin !== backendUrl) {
      event.preventDefault();
      shell.openExternal(navigationUrl);
    }
  });

  // Enable context menu
  contextMenu({
    window: mainWindow,
    showCopyImage: true,
    showCopyImageAddress: true,
    showSaveImageAs: true,
    showInspectElement: process.env.NODE_ENV === 'development'
  });

  return mainWindow;
}

function createTray() {
  const iconPath = path.join(__dirname, '../assets/tray-icon.png');
  let trayIcon;
  
  try {
    trayIcon = nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 });
  } catch (error) {
    console.log('Tray icon not found, using default');
    trayIcon = nativeImage.createEmpty();
  }
  
  tray = new Tray(trayIcon);
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show AI Assistant',
      click: () => {
        mainWindow.show();
        mainWindow.focus();
      }
    },
    {
      label: 'Voice Command',
      accelerator: 'CommandOrControl+Shift+V',
      click: () => {
        mainWindow.show();
        mainWindow.focus();
        mainWindow.webContents.send('trigger-voice-input');
      }
    },
    { type: 'separator' },
    {
      label: 'Preferences',
      click: () => {
        showPreferences();
      }
    },
    { type: 'separator' },
    {
      label: 'Quit AI Assistant',
      accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);
  
  tray.setContextMenu(contextMenu);
  tray.setToolTip('AI Ultimate Assistant');
  
  // Handle tray click
  tray.on('click', () => {
    if (mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Conversation',
          accelerator: 'CommandOrControl+N',
          click: () => {
            mainWindow.webContents.send('new-conversation');
          }
        },
        { type: 'separator' },
        {
          label: 'Preferences',
          accelerator: process.platform === 'darwin' ? 'Cmd+,' : 'Ctrl+,',
          click: showPreferences
        },
        { type: 'separator' },
        {
          role: 'quit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q'
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectall' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
        {
          label: 'Auto Hide Menu Bar',
          type: 'checkbox',
          checked: store.get('autoHideMenuBar', false),
          click: (item) => {
            store.set('autoHideMenuBar', item.checked);
            mainWindow.setAutoHideMenuBar(item.checked);
          }
        }
      ]
    },
    {
      label: 'AI Assistant',
      submenu: [
        {
          label: 'Voice Command',
          accelerator: 'CommandOrControl+Shift+V',
          click: () => {
            mainWindow.webContents.send('trigger-voice-input');
          }
        },
        {
          label: 'Quick Actions',
          accelerator: 'CommandOrControl+K',
          click: () => {
            mainWindow.webContents.send('show-quick-actions');
          }
        },
        { type: 'separator' },
        {
          label: 'Check for Updates',
          click: () => {
            autoUpdater.checkForUpdatesAndNotify();
          }
        }
      ]
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'close' },
        {
          label: 'Hide to Tray',
          accelerator: 'CommandOrControl+H',
          click: () => {
            mainWindow.hide();
          }
        }
      ]
    },
    {
      role: 'help',
      submenu: [
        {
          label: 'About AI Assistant',
          click: showAbout
        },
        {
          label: 'Learn More',
          click: () => {
            shell.openExternal('https://github.com/your-repo/ai-ultimate-assistant');
          }
        }
      ]
    }
  ];

  // macOS specific menu adjustments
  if (process.platform === 'darwin') {
    template.unshift({
      label: app.getName(),
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideothers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    });

    // Window menu for macOS
    template[5].submenu = [
      { role: 'close' },
      { role: 'minimize' },
      { role: 'zoom' },
      { type: 'separator' },
      { role: 'front' }
    ];
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function showPreferences() {
  // Create preferences window
  const preferencesWindow = new BrowserWindow({
    width: 500,
    height: 600,
    resizable: false,
    modal: true,
    parent: mainWindow,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  preferencesWindow.loadFile(path.join(__dirname, 'renderer/preferences.html'));
  preferencesWindow.setMenu(null);
}

function showAbout() {
  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'About AI Ultimate Assistant',
    message: 'AI Ultimate Assistant',
    detail: `Version: ${app.getVersion()}\nElectron: ${process.versions.electron}\nNode: ${process.versions.node}\n\nA comprehensive AI-powered assistant for managing Gmail, Calendar, Contacts, and Slack.`,
    buttons: ['OK']
  });
}

// Set app metadata for macOS permissions
app.setName('AI Ultimate Assistant');
if (process.platform === 'darwin') {
  app.setAboutPanelOptions({
    applicationName: 'AI Ultimate Assistant',
    applicationVersion: '1.0.0',
    copyright: '© 2024 AI Ultimate Assistant'
  });
}

// App event handlers
app.whenReady().then(async () => {
  createWindow();
  createMenu();
  createTray();
  
  // Request microphone permission on macOS
  await requestMicrophonePermission();
  
  // Handle auto-launch preference
  if (store.get('autoLaunch', false)) {
    autoLauncher.enable();
  }

  // Check for updates in production
  if (process.env.NODE_ENV !== 'development') {
    autoUpdater.checkForUpdatesAndNotify();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  } else {
    mainWindow.show();
  }
});

app.on('before-quit', () => {
  isQuitting = true;
});

// IPC handlers
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('get-store-value', (event, key, defaultValue) => {
  return store.get(key, defaultValue);
});

ipcMain.handle('set-store-value', (event, key, value) => {
  store.set(key, value);
});

ipcMain.handle('show-message-box', async (event, options) => {
  const result = await dialog.showMessageBox(mainWindow, options);
  return result;
});

ipcMain.handle('show-open-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options);
  return result;
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options);
  return result;
});

ipcMain.handle('open-external', async (event, url) => {
  await shell.openExternal(url);
  return true;
});

ipcMain.handle('reset-backend-url', () => {
      store.set('backendUrl', 'http://localhost:8000');
  return true;
});

// Auto-updater events
autoUpdater.on('checking-for-update', () => {
  console.log('Checking for update...');
});

autoUpdater.on('update-available', (info) => {
  console.log('Update available.');
});

autoUpdater.on('update-not-available', (info) => {
  console.log('Update not available.');
});

autoUpdater.on('error', (err) => {
  console.log('Error in auto-updater. ' + err);
});

autoUpdater.on('download-progress', (progressObj) => {
  let log_message = "Download speed: " + progressObj.bytesPerSecond;
  log_message = log_message + ' - Downloaded ' + progressObj.percent + '%';
  log_message = log_message + ' (' + progressObj.transferred + "/" + progressObj.total + ')';
  console.log(log_message);
});

autoUpdater.on('update-downloaded', (info) => {
  console.log('Update downloaded');
  autoUpdater.quitAndInstall();
}); 