"""Test with styling"""
import sys
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter
from PySide6.QtWebEngineWidgets import QWebEngineView
from core.terminal_widget import TerminalWidget

STYLE = """
QMainWindow { background: #0a0a0f; }
QSplitter { background: #0a0a0f; }
QSplitter::handle { background: #06b6d4; width: 3px; }
TerminalOutput, QTextEdit { background: #0d1117; color: #cdd6f4; border: 2px solid #06b6d4; }
QFrame#inputFrame { background: #161b22; border: 2px solid #06b6d4; }
TerminalInput, QLineEdit { background: #0d1117; color: #22d3ee; border: 1px solid #1e3a5f; }
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Style")
        self.resize(1000, 700)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.terminal = TerminalWidget()
        splitter.addWidget(self.terminal)

        self.web = QWebEngineView()
        self.web.setHtml("<h1 style='color:white;background:#1a1a2e;padding:20px'>Web</h1>")
        splitter.addWidget(self.web)
        splitter.setSizes([500, 500])
        self.setCentralWidget(splitter)

        self.setStyleSheet(STYLE)
        self.terminal.append_output("Styled terminal!", "system")

print("Starting...")
app = QApplication(sys.argv)
window = MainWindow()
window.show()
print("Window shown!")
sys.exit(app.exec())
