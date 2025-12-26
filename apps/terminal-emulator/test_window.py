"""Minimal window test"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("TEST WINDOW")
window.resize(400, 300)
window.setCentralWidget(QLabel("If you see this, Qt works!"))
window.show()
print("Window should be visible now!")
sys.exit(app.exec())
