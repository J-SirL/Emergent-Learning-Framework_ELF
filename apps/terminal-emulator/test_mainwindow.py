"""Test MainWindow class"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter
from PySide6.QtWebEngineWidgets import QWebEngineView
from core.terminal_widget import TerminalWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print("A. MainWindow.__init__ start")
        self.setWindowTitle("Test MainWindow")
        self.resize(1000, 700)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.terminal = TerminalWidget()
        splitter.addWidget(self.terminal)

        self.web = QWebEngineView()
        self.web.setHtml("<h1>Web</h1>")
        splitter.addWidget(self.web)
        splitter.setSizes([500, 500])

        self.setCentralWidget(splitter)
        print("B. MainWindow.__init__ done")

print("1. Starting")
app = QApplication(sys.argv)
print("2. App created")
window = MainWindow()
print("3. Window created")
window.show()
print("4. Window shown - should stay open!")
sys.exit(app.exec())
