# AI Ultimate Assistant - Desktop Application

A native desktop application built with Electron for the AI Ultimate Assistant. This provides a cross-platform desktop experience with enhanced features like system tray integration, keyboard shortcuts, and native notifications.

## 🚀 Features

- **Native Desktop Experience**: Full cross-platform support (Windows, macOS, Linux)
- **System Tray Integration**: Minimize to tray and quick access from system tray
- **Keyboard Shortcuts**: Global shortcuts for voice commands and quick actions
- **Native Notifications**: Desktop notifications for important updates
- **Persistent Settings**: Settings are automatically saved and restored
- **Auto-updater**: Automatic updates for new versions
- **Context Menus**: Right-click context menus with copy/paste support
- **Window State Management**: Remembers window size and position
- **Voice Integration**: Enhanced voice recognition and speech synthesis
- **Chat Export**: Export chat history to text files
- **Preferences Window**: Comprehensive settings management

## 📋 Prerequisites

- **Node.js**: Version 16 or higher
- **npm**: Version 7 or higher
- **Python**: Version 3.8+ (for native dependencies)
- **AI Assistant Backend**: The main AI assistant server must be running

## 🛠️ Installation

### 1. Navigate to Desktop Client Directory

```bash
cd desktop_client
```

### 2. Install Dependencies

```bash
npm install
```

This will install all required dependencies including:
- Electron framework
- Native modules for auto-launch, window state, etc.
- Build tools for cross-platform packaging

### 3. Start the Backend Server

Make sure the AI Assistant backend is running first:

```bash
# In the main ai_assistant directory
cd ../
python main.py
```

The backend should be running on `http://localhost:8000`

### 4. Run the Desktop Application

#### Development Mode
```bash
npm run dev
```

#### Production Mode
```bash
npm start
```

## 🏗️ Building for Distribution

### Build for Current Platform
```bash
npm run build
```

### Build for Specific Platforms

#### macOS
```bash
npm run build:mac
```

#### Windows
```bash
npm run build:win
```

#### Linux
```bash
npm run build:linux
```

### Build Artifacts

Built applications will be available in the `dist/` directory:
- **macOS**: `.dmg` installer
- **Windows**: `.exe` installer
- **Linux**: `.AppImage` and `.deb` packages

## ⚙️ Configuration

### Backend Connection

The desktop app connects to the AI Assistant backend. You can configure the connection:

1. Open **Preferences** (Cmd/Ctrl + ,)
2. Go to **General** tab
3. Update **Backend Server URL** (default: `http://localhost:8000`)

### Voice Settings

Customize voice recognition and speech synthesis:

1. Open **Preferences**
2. Go to **Voice** tab
3. Adjust speech rate, pitch, and volume
4. Test settings with the **Test Voice** button

### Desktop Settings

Configure desktop-specific features:

1. Open **Preferences**
2. Go to **Desktop** tab
3. Enable/disable:
   - Launch at startup
   - Minimize to system tray
   - Close to system tray
   - Desktop notifications
   - Auto-hide menu bar

## 🎯 Usage

### Main Interface

- **Chat Interface**: Type messages or use voice input
- **Quick Actions**: Pre-configured buttons for common tasks
- **Status Bar**: Shows connection status for all services
- **Voice Controls**: Speech recognition and text-to-speech

### Keyboard Shortcuts

- **Ctrl/Cmd + Shift + V**: Trigger voice input
- **Ctrl/Cmd + K**: Show quick actions
- **Ctrl/Cmd + N**: New conversation
- **Ctrl/Cmd + ,**: Open preferences
- **Ctrl/Cmd + H**: Hide to system tray
- **Escape**: Close modals/dialogs

### System Tray

The app can minimize to the system tray for quick access:

- **Click tray icon**: Show/hide window
- **Right-click tray icon**: Access context menu
- **Voice Command**: Trigger voice input from tray

### Voice Commands

Enhanced voice recognition with desktop-specific features:

- Natural language processing
- Automatic message sending after speech recognition
- Configurable speech synthesis for responses
- Global voice shortcuts

## 📁 Project Structure

```
desktop_client/
├── package.json              # Dependencies and build configuration
├── src/
│   ├── main.js              # Main Electron process
│   ├── preload.js           # Security layer for renderer
│   └── renderer/
│       ├── index.html       # Main application interface
│       ├── app.js          # Application logic
│       └── preferences.html # Settings window
├── assets/
│   ├── icon.png            # Application icon (Linux)
│   ├── icon.icns           # Application icon (macOS)
│   ├── icon.ico            # Application icon (Windows)
│   └── tray-icon.png       # System tray icon
├── build/                  # Build resources
└── dist/                   # Built applications (generated)
```

## 🔧 Development

### Development Mode

Run in development mode with hot reload:

```bash
npm run dev
```

### Debug Mode

Enable developer tools:
- **F12** or **Ctrl/Cmd + Shift + I**: Open DevTools
- **Ctrl/Cmd + R**: Reload window
- **Ctrl/Cmd + Shift + R**: Force reload

### Environment Variables

- `NODE_ENV=development`: Enable development features
- `ELECTRON_IS_DEV=1`: Enable Electron development mode

## 🚨 Troubleshooting

### Common Issues

#### 1. App Won't Start
- Ensure Node.js version 16+ is installed
- Run `npm install` to install dependencies
- Check if backend server is running

#### 2. Connection Failed
- Verify backend URL in preferences
- Ensure backend server is accessible
- Check firewall/network settings

#### 3. Voice Features Not Working
- Check microphone permissions
- Verify browser supports Web Speech API
- Test voice settings in preferences

#### 4. Build Failures
- Clear node_modules: `rm -rf node_modules && npm install`
- Update dependencies: `npm update`
- Check platform-specific build requirements

### System Requirements

#### Windows
- Windows 10 or later
- Visual Studio Build Tools (for native modules)

#### macOS
- macOS 10.14 or later
- Xcode Command Line Tools

#### Linux
- Ubuntu 18.04+ or equivalent
- Essential build tools: `build-essential`

## 🔒 Security

The desktop application follows Electron security best practices:

- **Context Isolation**: Renderer processes are isolated
- **Node Integration Disabled**: No Node.js access in renderer
- **Preload Scripts**: Secure API exposure via contextBridge
- **CSP Headers**: Content Security Policy enforcement
- **External Link Handling**: Opens external links in default browser

## 📦 Dependencies

### Core Dependencies
- **electron**: Desktop application framework
- **electron-store**: Settings persistence
- **electron-window-state**: Window state management
- **auto-launch**: Auto-startup functionality
- **electron-context-menu**: Enhanced context menus

### Development Dependencies
- **electron-builder**: Application packaging
- **electron-rebuild**: Native module rebuilding

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes in the `desktop_client` directory
4. Test thoroughly on target platforms
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the main LICENSE file for details.

## 🆘 Support

For desktop application issues:

1. Check this README for troubleshooting
2. Verify backend server connectivity
3. Check console for error messages
4. Report issues with system information:
   - Operating system and version
   - Node.js and npm versions
   - Electron version
   - Error messages and logs

---

**Happy productivity with your AI Ultimate Assistant Desktop App!** 🚀 