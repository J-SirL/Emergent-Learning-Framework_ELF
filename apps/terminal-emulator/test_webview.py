"""WebView test"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("WebView Test")
window.resize(800, 600)
web = QWebEngineView()
web.setHtml("<h1>WebView works!</h1>")
window.setCentralWidget(web)
window.show()
print("WebView window should be visible!")
sys.exit(app.exec())
