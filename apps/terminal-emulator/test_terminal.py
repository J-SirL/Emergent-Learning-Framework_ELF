"""Terminal without WebView test"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from core.terminal_widget import TerminalWidget

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Terminal Test")
window.resize(800, 600)
window.setCentralWidget(TerminalWidget())
window.show()
print("Terminal window should be visible!")
sys.exit(app.exec())
