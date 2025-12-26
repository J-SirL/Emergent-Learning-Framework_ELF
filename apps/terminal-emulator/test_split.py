"""Splitter test"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter
from PySide6.QtWebEngineWidgets import QWebEngineView
from core.terminal_widget import TerminalWidget

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Split Test")
window.resize(1000, 600)

splitter = QSplitter(Qt.Orientation.Horizontal)
splitter.addWidget(TerminalWidget())
web = QWebEngineView()
web.setHtml("<h1>Right panel</h1>")
splitter.addWidget(web)
splitter.setSizes([500, 500])

window.setCentralWidget(splitter)
window.show()
print("Split window should be visible!")
sys.exit(app.exec())
