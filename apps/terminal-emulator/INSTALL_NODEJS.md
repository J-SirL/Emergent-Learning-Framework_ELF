# Install Node.js - Quick Guide

Node.js is not currently installed on your system. Here's how to install it:

## Option 1: Official Installer (Recommended)

1. **Download Node.js:**
   - Go to: https://nodejs.org/
   - Download the **LTS version** (Long Term Support)
   - Choose Windows Installer (.msi) 64-bit

2. **Run the installer:**
   - Double-click the downloaded .msi file
   - Click "Next" through the wizard
   - ✅ Check "Automatically install necessary tools"
   - Click "Install"
   - Restart your terminal after installation

3. **Verify installation:**
   ```bash
   node --version
   npm --version
   ```

## Option 2: Using Winget (Windows Package Manager)

If you have Windows 11 or Windows 10 with winget:

```powershell
winget install OpenJS.NodeJS.LTS
```

## Option 3: Using Chocolatey

If you have Chocolatey installed:

```powershell
choco install nodejs-lts
```

## After Installation

Once Node.js is installed, continue with the terminal emulator setup:

```bash
# Navigate to the project
cd apps/terminal-emulator/ui/react

# Install dependencies
npm install

# Build the React app
npm run build

# Go back to root and run the app
cd ../..
python main.py
```

## Alternative: Skip React Build (Temporary)

If you want to test the Python backend without React:

```bash
cd apps/terminal-emulator
python demo.py
```

This will verify all Python components are working.

---

**Current Status:**
- ✅ Python backend: READY
- ✅ PySide6: INSTALLED
- ❌ Node.js: NOT INSTALLED (needed for React UI)

**Next Step:** Install Node.js from https://nodejs.org/
