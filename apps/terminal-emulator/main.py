"""
Terminal Emulator - Claude Chat Terminal
"""
import sys
import subprocess
import threading
from PySide6.QtCore import Qt, Slot, QObject, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter
from PySide6.QtWebEngineWidgets import QWebEngineView

from core.terminal_widget import TerminalWidget
from core.pty_worker import PTYWorker


class CommandRunner(QObject):
    """Run commands via subprocess (for non-interactive like claude -p)"""
    output = Signal(str)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, command: str):
        super().__init__()
        self.command = command
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            result = subprocess.run(
                self.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.stdout:
                self.output.emit(result.stdout)
            if result.stderr:
                self.output.emit(result.stderr)
            self.finished.emit(result.returncode)
        except subprocess.TimeoutExpired:
            self.error.emit("Command timed out")
            self.finished.emit(-1)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(-1)

    def is_running(self):
        return self._thread and self._thread.is_alive()


class TerminalController:
    """Claude chat mode controller"""

    def __init__(self, terminal: TerminalWidget):
        self.terminal = terminal
        self.worker = None
        self.claude_mode = True

        terminal.command_submitted.connect(self.run_command)
        terminal.input_submitted.connect(self.send_input)
        terminal.stop_requested.connect(self.stop)

    @Slot(str)
    def run_command(self, command: str):
        if not command.strip():
            return

        if command.strip() == "/shell":
            self.claude_mode = False
            self.terminal.append_output("Shell mode - type /claude to return", 'system')
            return
        elif command.strip() == "/claude":
            self.claude_mode = True
            self.terminal.append_output("Claude mode", 'system')
            return

        # Build command
        if self.claude_mode and not command.startswith("claude "):
            escaped = command.replace('"', '\\"')
            full_cmd = f'claude -p "{escaped}"'
            self.terminal.append_output(f"> {command}", 'command')
        else:
            full_cmd = command
            self.terminal.append_output(f"$ {command}", 'command')

        self.terminal.set_process_running(True)

        # Use subprocess for claude -p, PTY for interactive
        if "claude -p" in full_cmd:
            self.worker = CommandRunner(full_cmd)
            self.worker.output.connect(
                lambda t: self.terminal.append_output(t, 'stdout'),
                Qt.ConnectionType.QueuedConnection)
        else:
            self.worker = PTYWorker(full_cmd, cols=120, rows=30)
            self.worker.signals.output.connect(
                self.terminal.output.append_raw, Qt.ConnectionType.QueuedConnection)
            self.worker.signals.error.connect(
                lambda msg: self.terminal.append_output(msg, 'error'),
                Qt.ConnectionType.QueuedConnection)

        if hasattr(self.worker, 'signals'):
            self.worker.signals.finished.connect(
                self._on_finished, Qt.ConnectionType.QueuedConnection)
        else:
            self.worker.finished.connect(
                self._on_finished, Qt.ConnectionType.QueuedConnection)

        self.worker.start()

    @Slot(str)
    def send_input(self, data: str):
        if self.worker and hasattr(self.worker, 'write_line'):
            self.worker.write_line(data)

    @Slot()
    def stop(self):
        if self.worker:
            if hasattr(self.worker, 'stop'):
                self.worker.stop()
            if hasattr(self.worker, 'wait'):
                self.worker.wait(2000)
            self.worker = None
            self.terminal.append_output("^C", 'system')
            self.terminal.set_process_running(False)

    @Slot(int)
    def _on_finished(self, code: int):
        self.worker = None
        self.terminal.set_process_running(False)
        msg = f"[Exit code {code}]"
        self.terminal.append_output(msg, 'system' if code == 0 else 'error')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Claude Chat Terminal")
        self.resize(1200, 800)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.terminal = TerminalWidget()
        splitter.addWidget(self.terminal)

        self.webview = QWebEngineView()
        self.webview.setHtml("""
        <html><body style="background:#1a1a2e;color:#a855f7;font-family:sans-serif;
        display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
        <div style="text-align:center"><h1>Web Panel</h1><p style="color:#7dd3fc">Load any URL here</p></div>
        </body></html>
        """)
        splitter.addWidget(self.webview)
        splitter.setSizes([600, 600])

        self.setCentralWidget(splitter)

        self.controller = TerminalController(self.terminal)
        self.terminal.append_output("Claude Chat Terminal", 'system')
        self.terminal.append_output("Type anything to chat with Claude", 'system')
        self.terminal.append_output("/shell = shell mode  /claude = back to chat", 'system')
        self.terminal.append_output("", 'system')
        self.terminal.focus_input()

    def closeEvent(self, event):
        if self.controller.worker:
            self.controller.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
