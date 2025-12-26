"""
Configuration Management for Terminal Emulator
Handles environment variables and application settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""

    # Application
    APP_NAME = "Terminal Emulator"
    APP_VERSION = "1.0.0"

    # Development mode (load React from Vite dev server)
    DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

    # React UI URLs
    VITE_DEV_SERVER = "http://localhost:5173"
    REACT_BUILD_DIR = Path(__file__).parent / "ui" / "react" / "dist"

    # GitHub OAuth
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_REDIRECT_URI = "http://localhost:8765/callback"

    # Leaderboard Repository
    LEADERBOARD_REPO_OWNER = os.getenv("LEADERBOARD_REPO_OWNER", "")
    LEADERBOARD_REPO_NAME = os.getenv("LEADERBOARD_REPO_NAME", "")
    LEADERBOARD_FILE_PATH = "leaderboard.json"

    # Window settings
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"

    # Terminal settings
    MAX_OUTPUT_LINES = 5000  # Maximum lines to keep in terminal history

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GITHUB_CLIENT_ID and not cls.DEV_MODE:
            print("Warning: GITHUB_CLIENT_ID not set. GitHub OAuth will not work.")

        if cls.DEV_MODE:
            print(f"[DEV] Running in DEVELOPMENT mode - loading React from {cls.VITE_DEV_SERVER}")
        else:
            if not cls.REACT_BUILD_DIR.exists():
                print(f"[WARNING] React build directory not found: {cls.REACT_BUILD_DIR}")
                print("Run 'npm run build' in ui/react/ directory")
            else:
                print(f"[PROD] Running in PRODUCTION mode - loading React from {cls.REACT_BUILD_DIR}")

    @classmethod
    def get_react_url(cls):
        """Get the URL to load the React app from"""
        if cls.DEV_MODE:
            return cls.VITE_DEV_SERVER
        else:
            index_file = cls.REACT_BUILD_DIR / "index.html"
            return index_file.as_uri() if index_file.exists() else ""
