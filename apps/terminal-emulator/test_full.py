"""Full test with config and styling"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter
from PySide6.QtWebEngineWidgets import QWebEngineView
from core.terminal_widget import TerminalWidget
from config import Config

print("1. Importing done")

Config.validate()
print("2. Config validated")

app = QApplication(sys.argv)
print("3. QApplication created")

window = QMainWindow()
window.setWindowTitle(Config.WINDOW_TITLE)
window.resize(Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
print("4. Window created")

splitter = QSplitter(Qt.Orientation.Horizontal)
terminal = TerminalWidget()
splitter.addWidget(terminal)
print("5. Terminal added")

web = QWebEngineView()
web.setHtml("<h1>Web Panel</h1>")
splitter.addWidget(web)
splitter.setSizes([500, 500])
print("6. WebView added")

window.setCentralWidget(splitter)
print("7. Central widget set")

window.show()
print("8. Window shown!")

sys.exit(app.exec())
