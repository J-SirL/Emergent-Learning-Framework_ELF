# Terminal Emulator - Complete Setup Guide

Step-by-step instructions to get the terminal emulator running on your system.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.8 or higher installed
- [ ] Node.js 16 or higher installed
- [ ] Git installed (for cloning)
- [ ] Text editor (VS Code recommended)

### Verify Installations

```bash
python --version  # Should be 3.8+
node --version    # Should be 16+
npm --version     # Should be 7+
```

## 🚀 Installation Steps

### Step 1: Clone or Download

```bash
# If using git
git clone <repository-url>
cd terminal-emulator

# Or download and extract the ZIP file
```

### Step 2: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Install React Dependencies

```bash
cd ui/react
npm install
```

### Step 4: Configure Environment

```bash
# Copy example environment file
copy .env.example .env  # Windows
# cp .env.example .env  # Mac/Linux

# Edit .env in your text editor
notepad .env  # Windows
# nano .env   # Mac/Linux
```

**Set these values in .env:**

```env
DEV_MODE=true

# GitHub OAuth (optional - for leaderboard)
GITHUB_CLIENT_ID=your_client_id_here
GITHUB_CLIENT_SECRET=your_client_secret_here

# Leaderboard repo (optional)
LEADERBOARD_REPO_OWNER=your_username
LEADERBOARD_REPO_NAME=terminal-leaderboard
```

## 🎯 Running the Application

### Development Mode (Recommended for First Run)

**Terminal 1 - Start React Dev Server:**
```bash
cd ui/react
npm run dev
```

Keep this terminal open. You should see:
```
  VITE v5.0.8  ready in 500 ms
  ➜  Local:   http://localhost:5173/
```

**Terminal 2 - Start Python App:**
```bash
# Make sure DEV_MODE=true in .env
python main.py
```

A window should open with the terminal emulator!

### Production Mode

First, build the React app:

```bash
cd ui/react
npm run build
```

Then set `DEV_MODE=false` in `.env` and run:

```bash
python main.py
```

## ✅ Testing the App

Once the window opens:

1. **Type a simple command:**
   ```
   python --version
   ```
   Press Enter. You should see the Python version printed.

2. **Try a streaming command:**
   ```
   ping google.com
   ```
   You should see ping responses appearing in real-time.

3. **Stop a process:**
   Click the **Stop** button or press Ctrl+C

4. **Test command history:**
   Press Arrow Up to see previous command

## 🐛 Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'PySide6'"

**Solution:**
```bash
pip install PySide6
```

### Issue: "Cannot find module" when running npm install

**Solution:**
```bash
cd ui/react
rm -rf node_modules package-lock.json
npm install
```

### Issue: Window opens but shows "React App Not Found"

**Solution:**
```bash
# If DEV_MODE=true:
cd ui/react
npm run dev
# Make sure Vite server is running at http://localhost:5173

# If DEV_MODE=false:
cd ui/react
npm run build
# Then restart Python app
```

### Issue: "QWebChannel not available"

**Cause:** Trying to open React app directly in browser instead of PySide6 window

**Solution:** Always run through `python main.py`, not by opening index.html in browser

### Issue: Commands don't work

**Check:**
1. Is the command in your PATH?
2. Try absolute path: `C:\Python39\python.exe --version`
3. Check if command exists: `where python` (Windows) or `which python` (Mac/Linux)

### Issue: Hot reloading not working

**Solution:**
1. Ensure `DEV_MODE=true` in `.env`
2. Restart Python app after changing `.env`
3. Check Vite dev server is running
4. Clear browser cache (in QWebEngineView: delete `~/.QtWebEngine` folder)

## 🎨 Customizing

### Change Theme Colors

Edit `ui/react/src/styles/terminal.css`:

```css
:root {
  --bg-primary: #1e1e2e;  /* Your color here */
}
```

Save and see changes instantly (dev mode) or rebuild (production).

### Change Window Size

Edit `config.py`:

```python
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
```

Restart the Python app.

## 🏆 GitHub Leaderboard Setup (Optional)

### Step 1: Create OAuth App

1. Go to https://github.com/settings/developers
2. Click **New OAuth App**
3. Fill in:
   - **Application name:** Terminal Emulator
   - **Homepage URL:** http://localhost
   - **Authorization callback URL:** `http://localhost:8765/callback`
4. Click **Register application**
5. Copy **Client ID** and click **Generate a new client secret**
6. Copy **Client Secret**
7. Paste both into `.env`:
   ```env
   GITHUB_CLIENT_ID=your_copied_client_id
   GITHUB_CLIENT_SECRET=your_copied_secret
   ```

### Step 2: Create Leaderboard Repository

1. Go to https://github.com/new
2. Repository name: `terminal-leaderboard` (or any name)
3. **Make it PUBLIC** ✅
4. Click **Create repository**
5. Create a file named `leaderboard.json` with content:
   ```json
   []
   ```
6. Commit the file
7. Update `.env`:
   ```env
   LEADERBOARD_REPO_OWNER=your_github_username
   LEADERBOARD_REPO_NAME=terminal-leaderboard
   ```

### Step 3: Test Leaderboard

1. Restart the Python app
2. Click **Show Leaderboard** in the app
3. Click **Login with GitHub**
4. Follow the OAuth flow
5. Submit a test score

## 📦 Building for Distribution

### Step 1: Build React App

```bash
cd ui/react
npm run build
```

This creates `ui/react/dist/` with optimized files.

### Step 2: Run PyInstaller

```bash
# Make sure you're in the root directory (with main.py)
pyinstaller terminal-emulator.spec
```

This creates:
- `dist/TerminalEmulator/` folder with the app
- `dist/TerminalEmulator/TerminalEmulator.exe` is the main executable

### Step 3: Test the Build

```bash
cd dist/TerminalEmulator
./TerminalEmulator.exe
```

The app should work standalone!

### Step 4: Distribute

Zip the entire `dist/TerminalEmulator/` folder and distribute.

**Include:**
- ✅ The entire `dist/TerminalEmulator/` folder
- ✅ `LICENSE.txt` (LGPL compliance)
- ✅ Instructions for users

## 🎓 Next Steps

Now that you have it running:

1. **Experiment with commands** - Try different shell commands
2. **Customize the theme** - Make it your own
3. **Add custom features** - Extend the Python code
4. **Build and distribute** - Share with others

## 📚 Resources

- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)

## 💡 Tips

- **Development:** Use `DEV_MODE=true` for instant React updates
- **Production:** Build React first, then set `DEV_MODE=false`
- **Debugging:** Check terminal output for Python errors
- **Performance:** Close unnecessary apps if UI is slow
- **Updates:** Pull latest code and run `npm install` + `pip install -r requirements.txt`

---

**Need help?** Check the README.md or create an issue in the repository.

**Happy coding! 🚀**
