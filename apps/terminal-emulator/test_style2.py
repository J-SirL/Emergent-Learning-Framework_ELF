"""Test minimal styling"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter
from PySide6.QtWebEngineWidgets import QWebEngineView
from core.terminal_widget import TerminalWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Style")
        self.resize(1000, 700)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.terminal = TerminalWidget()
        splitter.addWidget(self.terminal)

        self.web = QWebEngineView()
        self.web.setHtml("<h1>Web</h1>")
        splitter.addWidget(self.web)
        splitter.setSizes([500, 500])
        self.setCentralWidget(splitter)

        # Minimal style - just background
        self.setStyleSheet("QMainWindow { background: #0a0a0f; }")
        self.terminal.append_output("Test!", "system")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
print("Shown!")
sys.exit(app.exec())
