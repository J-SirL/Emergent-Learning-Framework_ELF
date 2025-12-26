"""Test with controller"""
import sys
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter
from PySide6.QtWebEngineWidgets import QWebEngineView
from core.terminal_widget import TerminalWidget
from core.pty_worker import PTYWorker

class TerminalController:
    def __init__(self, terminal):
        self.terminal = terminal
        self.worker = None
        terminal.command_submitted.connect(self.run_command)

    @Slot(str)
    def run_command(self, cmd):
        print(f"Command: {cmd}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Controller")
        self.resize(1000, 700)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.terminal = TerminalWidget()
        splitter.addWidget(self.terminal)

        self.web = QWebEngineView()
        self.web.setHtml("<h1>Web</h1>")
        splitter.addWidget(self.web)
        splitter.setSizes([500, 500])
        self.setCentralWidget(splitter)

        # Add controller
        self.controller = TerminalController(self.terminal)
        self.terminal.append_output("Type something!", "system")

print("Starting...")
app = QApplication(sys.argv)
window = MainWindow()
window.show()
print("Window shown!")
sys.exit(app.exec())
