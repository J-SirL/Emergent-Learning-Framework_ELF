"""
PTY Worker - ConPTY process execution via pywinpty
"""
import shutil
from PySide6.QtCore import QObject, Signal, QThread


class PTYSignals(QObject):
    output = Signal(str)
    finished = Signal(int)
    error = Signal(str)
    started = Signal()


class PTYWorker(QThread):
    """Worker thread for interactive PTY programs"""

    def __init__(self, command: str, cwd: str = None, cols: int = 120, rows: int = 30):
        super().__init__()
        self.command = command
        self.cwd = cwd
        self.cols, self.rows = cols, rows
        self.signals = PTYSignals()
        self.pty = None
        self._stop = False

    def run(self):
        try:
            import winpty
        except ImportError:
            self.signals.error.emit("pywinpty not installed. Run: pip install pywinpty")
            return

        try:
            self.pty = winpty.PTY(cols=self.cols, rows=self.rows)

            # Parse command
            parts = self.command.split(None, 1)
            if not parts:
                self.signals.error.emit("Empty command")
                return

            cmd, args = parts[0], parts[1] if len(parts) > 1 else None

            # Find executable
            exe = shutil.which(cmd) or shutil.which(cmd + ".exe")
            if not exe:
                exe = shutil.which("cmd.exe")
                args = f"/c {self.command}"

            if not exe:
                self.signals.error.emit(f"Command not found: {cmd}")
                return

            if not self.pty.spawn(appname=exe, cmdline=args, cwd=self.cwd):
                self.signals.error.emit(f"Failed to spawn: {self.command}")
                return

            self.signals.started.emit()

            # Read loop
            while not self._stop:
                try:
                    data = self.pty.read(blocking=False)
                    if data:
                        self.signals.output.emit(data)
                    elif not self.pty.isalive():
                        break
                    else:
                        self.msleep(20)
                except Exception as e:
                    if "EOF" in str(e) or not self.pty.isalive():
                        break
                    self.msleep(50)

            # Drain remaining output
            for _ in range(20):
                try:
                    data = self.pty.read(blocking=False)
                    if data:
                        self.signals.output.emit(data)
                    else:
                        break
                except:
                    break

            self.signals.finished.emit(self.pty.get_exitstatus() or 0)

        except Exception as e:
            self.signals.error.emit(str(e))

    def write(self, data: str) -> bool:
        if self.pty and self.pty.isalive():
            try:
                self.pty.write(data)
                return True
            except:
                pass
        return False

    def write_line(self, data: str) -> bool:
        return self.write(data + "\n")

    def resize(self, cols: int, rows: int):
        if self.pty:
            try:
                self.pty.set_size(cols, rows)
                self.cols, self.rows = cols, rows
            except:
                pass

    def stop(self):
        self._stop = True
        if self.pty:
            try:
                self.pty.write("\x03")
            except:
                pass

    def is_running(self) -> bool:
        return self.pty is not None and self.pty.isalive()
