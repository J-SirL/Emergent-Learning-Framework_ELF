# Terminal Emulator - PySide6 + React

A professional, customizable terminal emulator with a beautiful modern UI built with PySide6 (Qt for Python) and React + TypeScript. Features real-time subprocess execution, GitHub OAuth leaderboard, and hot reloading for development.

## ✨ Features

- **Modern Dark Terminal UI** - Beautiful Catppuccin-inspired theme with custom styling
- **Real-time Process Execution** - Run commands and stream stdout/stderr without freezing
- **ANSI Color Support** - Full support for terminal color codes and styling
- **User Input/Output** - Send input to running processes via stdin
- **Command History** - Arrow up/down to navigate command history
- **GitHub Leaderboard** - OAuth authentication and public leaderboard (no backend needed)
- **Hot Reloading** - React changes appear instantly during development
- **Cross-platform** - Works on Windows, macOS, and Linux
- **Single .exe Distribution** - Package as standalone executable with PyInstaller

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│          PySide6 QMainWindow            │
│  ┌───────────────────────────────────┐  │
│  │   QWebEngineView (React App)      │  │
│  │                                   │  │
│  │   React + TypeScript + Vite       │  │
│  │   • Terminal UI                   │  │
│  │   • ANSI rendering                │  │
│  │   • Input handling                │  │
│  │   • Leaderboard                   │  │
│  └───────────────────────────────────┘  │
│                                         │
│         QWebChannel (Bridge)            │
│        Python ↔ JavaScript              │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │   TerminalManager                 │  │
│  │   • ProcessWorker (QRunnable)     │  │
│  │   • stdout/stderr streaming       │  │
│  │   • stdin handling                │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │   GitHub API                      │  │
│  │   • OAuth flow                    │  │
│  │   • Leaderboard (Contents API)    │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 16+** (for React development)
- **Bun** (recommended) or **npm** (for React build)

## 🚀 Quick Start

### 1. Install Python Dependencies

```bash
cd terminal-emulator
pip install -r requirements.txt
```

### 2. Install React Dependencies

```bash
cd ui/react
npm install
# or
bun install
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in your GitHub OAuth credentials
```

### 4. Run in Development Mode

**Terminal 1 - Start React Dev Server:**
```bash
cd ui/react
npm run dev
# React will run at http://localhost:5173
```

**Terminal 2 - Start PySide6 App:**
```bash
# Make sure DEV_MODE=true in .env
python main.py
```

The PySide6 window will load the React app from the Vite dev server with hot reloading!

## 🔧 Development Workflow

### Development Mode (Recommended)

1. Set `DEV_MODE=true` in `.env`
2. Run `npm run dev` in `ui/react/`
3. Run `python main.py`
4. Edit React files - changes appear instantly without restarting Python app

### Production Build

1. Build React app:
   ```bash
   cd ui/react
   npm run build
   ```

2. Set `DEV_MODE=false` in `.env`

3. Run Python app:
   ```bash
   python main.py
   ```

## 🎯 Usage

### Running Commands

Type any shell command in the input bar:

```
ping google.com
python --version
dir  # Windows
ls -la  # Unix
node -v
npm --version
```

### Command History

- **Arrow Up** - Previous command
- **Arrow Down** - Next command
- **Enter** - Execute command

### Sending Input to Process

If a process is waiting for input (e.g., Python script with `input()`), type your input and press Enter. It will be sent to the process stdin.

### Stopping Process

- Click **Stop** button
- Press **Ctrl+C** in input field

## 🏆 GitHub Leaderboard Setup

### 1. Create GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Click **New OAuth App**
3. Fill in:
   - Application name: `Terminal Emulator`
   - Homepage URL: `http://localhost`
   - Authorization callback URL: `http://localhost:8765/callback`
4. Copy **Client ID** and **Client Secret** to `.env`

### 2. Create Leaderboard Repository

1. Create a new **public** GitHub repository (e.g., `terminal-leaderboard`)
2. Create an empty `leaderboard.json` file:
   ```json
   []
   ```
3. Update `.env` with your repository info:
   ```
   LEADERBOARD_REPO_OWNER=your_username
   LEADERBOARD_REPO_NAME=terminal-leaderboard
   ```

### 3. Submit Scores

```python
# In your Python code:
bridge.submit_score("username", 1000)

# Or from React:
github.submitScore(1000);
```

Scores are automatically stored in the GitHub repository as JSON.

## 📦 Building for Distribution

### PyInstaller Configuration

Create a standalone Windows `.exe`:

```bash
pyinstaller terminal-emulator.spec
```

The `.spec` file is pre-configured for:
- Single-file or folder distribution
- Including React build files
- LGPL compliance (PySide6 remains dynamically linked)

### Distribution Structure

```
dist/
└── TerminalEmulator/
    ├── TerminalEmulator.exe
    ├── ui/
    │   └── react/
    │       └── dist/  # Built React files
    └── [PySide6 DLLs]
```

### LGPL Compliance

PySide6 is licensed under LGPL. To comply:

1. ✅ **Do not statically link** - PyInstaller keeps DLLs separate (default)
2. ✅ **Include LICENSE.txt** - LGPL notice provided
3. ✅ **Provide source or instructions** - Link to this repo
4. ✅ **Commercial use allowed** - Your code can be closed-source

This setup allows you to:
- Sell the app commercially
- Keep your application code proprietary
- Distribute as a single folder or installer

## 🎨 Customization

### Theme Colors

Edit `ui/react/src/styles/terminal.css`:

```css
:root {
  --bg-primary: #1e1e2e;      /* Main background */
  --bg-secondary: #181825;    /* Secondary background */
  --accent-blue: #89b4fa;     /* Primary accent */
  --accent-green: #a6e3a1;    /* Success color */
  --accent-red: #f38ba8;      /* Error color */
}
```

### Window Size

Edit `config.py`:

```python
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
```

### ANSI Colors

Customize in `terminal.css` under `/* ANSI Colors */`

## 🔌 API Reference

### Python → JavaScript (Signals)

```python
# Emit output
bridge.outputReceived.emit("Hello", "stdout")

# Emit process finished
bridge.processFinished.emit(0)

# Emit error
bridge.processError.emit("Error message")

# Update leaderboard
bridge.leaderboardUpdated.emit(json.dumps(data))

# Auth status
bridge.authStatusChanged.emit(True, "username")
```

### JavaScript → Python (Methods)

```typescript
// Run command
bridge.runCommand("ping google.com");

// Send stdin
bridge.sendInput("hello");

// Stop process
bridge.stopProcess();

// Submit score
bridge.submitScore("username", 1000);

// Auth
bridge.authenticateGitHub(accessToken);
bridge.logout();

// Getters
bridge.isAuthenticated();
bridge.getUsername();
bridge.getVersion();
```

## 🐛 Troubleshooting

### "QWebChannel not available"

- Make sure you're running inside the PySide6 app, not a regular browser
- Check that `qwebchannel.js` script tag is in `index.html`

### React build not found

```bash
cd ui/react
npm run build
```

Make sure `DEV_MODE=false` in `.env` for production builds.

### Hot reloading not working

- Ensure `DEV_MODE=true` in `.env`
- Check Vite dev server is running at `http://localhost:5173`
- Restart Python app after changing `.env`

### Process hangs

- Use **Stop** button or Ctrl+C
- Check that subprocess is not waiting for input
- Some interactive programs may not work well (use direct terminal instead)

## 📝 License

**Application Code:** MIT License (your code)

**PySide6:** LGPL v3 - dynamically linked, allows commercial use

**React:** MIT License

See `LICENSE.txt` for full LGPL compliance notice.

## 🙏 Credits

- **PySide6** - Qt for Python (LGPL)
- **React** - UI library (MIT)
- **Vite** - Build tool (MIT)
- **Catppuccin** - Color scheme inspiration

## 🚀 Advanced Features

### Custom Commands

Add custom commands in `core/terminal_manager.py`:

```python
def run_command(self, command_str):
    if command_str == "hello":
        self.web_bridge.emit_output("Hello, World!", "system")
        return

    # ... rest of implementation
```

### Process Monitoring

Hook into process signals:

```python
self.current_worker.signals.stdout.connect(self.on_stdout)
```

### GitHub Webhooks

Extend `utils/github_api.py` for webhook events.

## 📚 Resources

- [PySide6 Docs](https://doc.qt.io/qtforpython/)
- [QWebChannel Docs](https://doc.qt.io/qt-6/qwebchannel.html)
- [Vite Docs](https://vitejs.dev/)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)

---

**Built with ❤️ using PySide6 and React**
