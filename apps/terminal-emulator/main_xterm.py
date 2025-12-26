"""
Terminal Emulator - xterm.js + PySide6 Split Pane
Uses WebSocket bridge to connect xterm.js to ConPTY
Modern UI with Catppuccin Mocha theme
"""
import sys
import threading
import asyncio
import socket
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QTimer, QObject, Signal, Slot, QPoint
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineNewWindowRequest
from PySide6.QtWebChannel import QWebChannel

from core.pty_server import PTYWebSocketServer


# Catppuccin Mocha color scheme
COLORS = {
    'base': '#1e1e2e',
    'mantle': '#181825',
    'surface0': '#313244',
    'surface1': '#45475a',
    'surface2': '#585b70',
    'text': '#cdd6f4',
    'subtext0': '#a6adc8',
    'subtext1': '#bac2de',
    'lavender': '#b4befe',
    'mauve': '#cba6f7',
    'pink': '#f5c2e7',
    'red': '#f38ba8',
    'green': '#a6e3a1',
    'yellow': '#f9e2af',
    'blue': '#89b4fa',
    'teal': '#94e2d5',
}


class TitleBar(QWidget):
    """Custom title bar with window controls"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.dragging = False
        self.drag_position = QPoint()

        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['base']};
                border-bottom: 1px solid {COLORS['surface0']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(12)

        # App icon placeholder (you can add an actual icon here)
        icon_label = QLabel("⚡")
        icon_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['mauve']};
                font-size: 20px;
                border: none;
            }}
        """)
        layout.addWidget(icon_label)

        # Title
        title = QLabel("Claude Terminal")
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text']};
                font-size: 14px;
                font-weight: 600;
                border: none;
            }}
        """)
        layout.addWidget(title)

        # Stretch to push buttons to the right
        layout.addStretch()

        # Window controls
        btn_style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {COLORS['subtext0']};
                font-size: 16px;
                padding: 4px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['surface0']};
                color: {COLORS['text']};
            }}
        """
        close_btn_style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {COLORS['subtext0']};
                font-size: 16px;
                padding: 4px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['red']};
                color: {COLORS['base']};
            }}
        """

        # Minimize button
        min_btn = QPushButton("−")
        min_btn.setStyleSheet(btn_style)
        min_btn.setFixedSize(40, 32)
        min_btn.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(min_btn)

        # Maximize button
        self.max_btn = QPushButton("□")
        self.max_btn.setStyleSheet(btn_style)
        self.max_btn.setFixedSize(40, 32)
        self.max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.max_btn)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet(close_btn_style)
        close_btn.setFixedSize(40, 32)
        close_btn.clicked.connect(self.parent_window.close)
        layout.addWidget(close_btn)

    def _toggle_maximize(self):
        """Toggle between maximized and normal"""
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.max_btn.setText("□")
        else:
            self.parent_window.showMaximized()
            self.max_btn.setText("❐")

    def mousePressEvent(self, event):
        """Start dragging window"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Drag window"""
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Stop dragging"""
        self.dragging = False
        event.accept()

    def mouseDoubleClickEvent(self, event):
        """Double-click to maximize"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
            event.accept()


class StatusBar(QWidget):
    """Custom status bar showing connection status"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['mantle']};
                border-top: 1px solid {COLORS['surface0']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(16)

        # Connection status indicator
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['green']};
                font-size: 12px;
                border: none;
            }}
        """)
        layout.addWidget(self.status_dot)

        # Status text
        self.status_label = QLabel("Connected")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['subtext0']};
                font-size: 12px;
                border: none;
            }}
        """)
        layout.addWidget(self.status_label)

        # Stretch
        layout.addStretch()

        # Port info
        self.port_label = QLabel("")
        self.port_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['surface2']};
                font-size: 11px;
                border: none;
            }}
        """)
        layout.addWidget(self.port_label)

    def set_connected(self, port: int):
        """Update status to connected"""
        self.status_dot.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['green']};
                font-size: 12px;
                border: none;
            }}
        """)
        self.status_label.setText("Connected")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['subtext0']};
                font-size: 12px;
                border: none;
            }}
        """)
        self.port_label.setText(f"Port {port}")

    def set_disconnected(self):
        """Update status to disconnected"""
        self.status_dot.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['red']};
                font-size: 12px;
                border: none;
            }}
        """)
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['red']};
                font-size: 12px;
                border: none;
            }}
        """)


class UrlBridge(QObject):
    """Bridge for URL messages from terminal to dashboard"""
    url_received = Signal(str)

    @Slot(str)
    def openUrl(self, url: str):
        """Called from JavaScript when URL should be opened"""
        print(f"[URL Bridge] Opening: {url}")
        self.url_received.emit(url)


class InternalWebPage(QWebEnginePage):
    """Custom page that keeps all navigation internal to the webview"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._view = parent
        # Connect the new window request signal
        self.newWindowRequested.connect(self._handle_new_window)

    def _handle_new_window(self, request: QWebEngineNewWindowRequest):
        """Handle requests for new windows - load in same view instead"""
        url = request.requestedUrl()
        print(f"[InternalWebPage] Intercepted new window request: {url.toString()}")
        # Load the URL in the same view instead of opening external window
        if self._view:
            self._view.setUrl(url)

    def acceptNavigationRequest(self, url: QUrl, nav_type: QWebEnginePage.NavigationType, is_main_frame: bool) -> bool:
        """Accept all navigation requests to keep everything internal"""
        print(f"[InternalWebPage] Navigation: {url.toString()} (type={nav_type}, main_frame={is_main_frame})")
        return True


def find_free_port(start: int = 8765, end: int = 8865) -> int:
    """Find an available port"""
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError("No free ports available")


class WebSocketServerThread(threading.Thread):
    """Run WebSocket server in background thread"""

    def __init__(self, port: int):
        super().__init__(daemon=True)
        self.port = port
        self.server = PTYWebSocketServer(
            port=port,
            startup_command="claude",
            startup_input="checkin\n"
        )
        self._loop = None

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self.server.start())
        except Exception as e:
            print(f"Server error: {e}")

    def stop(self):
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)


class TerminalWebView(QWebEngineView):
    """WebView configured for xterm.js terminal"""

    def __init__(self, port: int, url_bridge: UrlBridge = None, parent=None):
        super().__init__(parent)
        self.port = port
        self.url_bridge = url_bridge

        # Configure settings
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)

        # Setup QWebChannel for JS-Python communication
        if url_bridge:
            self.channel = QWebChannel()
            self.channel.registerObject("urlBridge", url_bridge)
            self.page().setWebChannel(self.channel)

        # Find xterm.html
        xterm_html = Path(__file__).parent / "ui" / "xterm" / "index.html"
        if not xterm_html.exists():
            print(f"Warning: xterm.html not found at {xterm_html}")
            self.setHtml(self._error_html("xterm.html not found"))
            return

        # Load with port parameter
        url = QUrl.fromLocalFile(str(xterm_html))
        url.setQuery(f"port={port}")
        self.setUrl(url)

    def _error_html(self, message: str) -> str:
        return f"""
        <html><body style="background:#1e1e2e;color:#f38ba8;font-family:monospace;
        display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
        <div style="text-align:center">
            <h1>Terminal Error</h1>
            <p>{message}</p>
        </div>
        </body></html>
        """


class DashboardWebView(QWebEngineView):
    """WebView for dashboard/web panel"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Use custom page to intercept new window requests
        self._page = InternalWebPage(self)
        self.setPage(self._page)

        # Configure settings for external URL loading
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)

        # Default content
        self.setHtml("""
        <html><body style="background:#1a1a2e;color:#a855f7;font-family:sans-serif;
        display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
        <div style="text-align:center">
            <h1 style="font-size:2rem;margin-bottom:1rem">Web Panel</h1>
            <p style="color:#7dd3fc">Load any URL or your ELF Dashboard</p>
            <p style="color:#585b70;margin-top:2rem;font-size:0.8rem">
                Left pane: Claude Code terminal<br>
                Right pane: Dashboard / Browser
            </p>
        </div>
        </body></html>
        """)

    def load_dashboard(self, port: int = 5173):
        """Load ELF dashboard"""
        self.setUrl(QUrl(f"http://localhost:{port}"))

    def load_url(self, url: str):
        """Load arbitrary URL"""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.setUrl(QUrl(url))


class MainWindow(QMainWindow):
    """Main application window with split terminal + web view"""

    def __init__(self):
        super().__init__()

        # Set frameless window with rounded corners
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setWindowTitle("Claude Terminal")
        self.resize(1400, 900)

        # Find free port and start WebSocket server
        self.ws_port = find_free_port()
        print(f"Starting PTY server on port {self.ws_port}")
        self.server_thread = WebSocketServerThread(self.ws_port)
        self.server_thread.start()

        # Wait a moment for server to start
        QTimer.singleShot(500, self._setup_ui)

    def _setup_ui(self):
        """Setup UI after server is ready"""
        # Main container with rounded background
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['base']};
                border-radius: 12px;
            }}
        """)

        # Apply shadow effect to window
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 160))
        container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom title bar
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['surface0']};
                width: 1px;
            }}
            QSplitter::handle:hover {{
                background-color: {COLORS['mauve']};
                width: 2px;
            }}
            QSplitter::handle:pressed {{
                background-color: {COLORS['mauve']};
                width: 3px;
            }}
        """)

        # Create URL bridge for terminal -> dashboard communication
        self.url_bridge = UrlBridge()

        # Right: Dashboard/web view (create first so we can connect signal)
        self.dashboard = DashboardWebView()

        # Connect URL bridge to dashboard
        self.url_bridge.url_received.connect(self.dashboard.load_url)

        # Left: xterm.js terminal with URL bridge
        self.terminal = TerminalWebView(self.ws_port, url_bridge=self.url_bridge)
        splitter.addWidget(self.terminal)
        splitter.addWidget(self.dashboard)

        # 50/50 split
        splitter.setSizes([700, 700])

        main_layout.addWidget(splitter)

        # Custom status bar
        self.status_bar = StatusBar()
        self.status_bar.set_connected(self.ws_port)
        main_layout.addWidget(self.status_bar)

        self.setCentralWidget(container)

        # Auto-load ELF dashboard after 1.5 seconds
        QTimer.singleShot(1500, lambda: self.dashboard.load_dashboard(3001))

    def closeEvent(self, event):
        """Clean shutdown"""
        print("Shutting down...")
        self.server_thread.stop()
        event.accept()


def main():
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Claude Terminal")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
