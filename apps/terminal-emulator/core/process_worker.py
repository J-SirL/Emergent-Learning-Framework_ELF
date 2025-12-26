"""
Process Worker - QRunnable for non-blocking subprocess execution
Runs external commands and streams stdout/stderr in real-time
"""
import subprocess
import sys
import shutil
import os
from PySide6.QtCore import QRunnable, QObject, Signal, Slot


# Windows shell built-in commands that need cmd /c wrapper
WINDOWS_BUILTINS = {
    'dir', 'cd', 'cls', 'copy', 'del', 'echo', 'md', 'mkdir',
    'move', 'rd', 'rmdir', 'ren', 'rename', 'type', 'vol',
    'date', 'time', 'ver', 'set', 'path', 'prompt', 'title',
    'color', 'start', 'assoc', 'ftype', 'pushd', 'popd',
}


class ProcessSignals(QObject):
    """Signals for communicating from worker thread to main thread"""
    stdout = Signal(str)  # Emitted when stdout data is received
    stderr = Signal(str)  # Emitted when stderr data is received
    finished = Signal(int)  # Emitted when process finishes (exit code)
    error = Signal(str)  # Emitted when an error occurs


class ProcessWorker(QRunnable):
    """
    Worker thread for running subprocesses without blocking the GUI.

    Usage:
        worker = ProcessWorker(["python", "-c", "print('Hello')"])
        worker.signals.stdout.connect(handle_output)
        worker.signals.finished.connect(handle_finish)
        QThreadPool.globalInstance().start(worker)
    """

    def __init__(self, command, cwd=None):
        """
        Initialize the process worker.

        Args:
            command: List of command arguments (e.g., ["ping", "google.com"])
            cwd: Working directory for the command (optional)
        """
        super().__init__()
        self.original_command = command
        self.command = self._prepare_command(command)
        self.cwd = cwd
        self.signals = ProcessSignals()
        self.process = None
        self._stop_requested = False

    def _prepare_command(self, command):
        """Prepare command for execution, handling Windows shell built-ins"""
        if sys.platform == 'win32' and command:
            cmd_name = command[0].lower()
            # Check if it's a Windows shell built-in
            if cmd_name in WINDOWS_BUILTINS:
                # Wrap in cmd /c for shell built-ins
                return ['cmd', '/c'] + command
        return command

    def stop(self):
        """Request the process to stop"""
        self._stop_requested = True
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()

    @Slot()
    def run(self):
        """
        Execute the command and stream output.
        This runs in a background thread.
        """
        print(f"[ProcessWorker] Starting process: {self.command}")
        print(f"[ProcessWorker] Original command: {self.original_command}")
        try:
            # Check if command exists before trying to run it
            # Skip check for Windows shell built-ins (they're handled via cmd /c)
            original_cmd_name = self.original_command[0].lower() if self.original_command else ''
            if original_cmd_name not in WINDOWS_BUILTINS:
                command_name = self.command[0]
                command_path = shutil.which(command_name)
                print(f"[ProcessWorker] shutil.which('{command_name}') = {command_path}")
                if not command_path:
                    print(f"[ProcessWorker] Command not found in PATH: {command_name}")
                    self.signals.error.emit(f"Command not found: {command_name}")
                    return
            else:
                print(f"[ProcessWorker] Shell built-in detected: {original_cmd_name}")

            # Start the process
            print(f"[ProcessWorker] Creating Popen...")
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                cwd=self.cwd,
                shell=False,  # Security: never use shell=True with user input
                universal_newlines=True
            )

            # Use communicate() to avoid deadlocks
            # This waits for the process to complete and gets all output
            print(f"[ProcessWorker] Waiting for process to complete...")
            stdout, stderr = self.process.communicate()

            print(f"[ProcessWorker] Process completed")

            # Emit all output
            if stdout:
                print(f"[ProcessWorker] STDOUT ({len(stdout)} chars):")
                for line in stdout.splitlines():
                    print(f"  > {line}")
                    self.signals.stdout.emit(line)

            if stderr:
                print(f"[ProcessWorker] STDERR ({len(stderr)} chars):")
                for line in stderr.splitlines():
                    print(f"  > {line}")
                    self.signals.stderr.emit(line)

            # Get exit code
            exit_code = self.process.returncode
            print(f"[ProcessWorker] Process finished with exit code: {exit_code}")
            self.signals.finished.emit(exit_code)

        except FileNotFoundError as e:
            print(f"[ProcessWorker] FileNotFoundError: {self.command[0]}")
            self.signals.error.emit(f"Command not found: {self.command[0]}")
        except Exception as e:
            print(f"[ProcessWorker] Exception: {type(e).__name__}: {str(e)}")
            self.signals.error.emit(f"Error executing command: {str(e)}")
        finally:
            if self.process:
                try:
                    self.process.stdout.close()
                    self.process.stderr.close()
                    self.process.stdin.close()
                except:
                    pass

    def write_stdin(self, data):
        """
        Write data to process stdin.

        Args:
            data: String to write to stdin
        """
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(data + '\n')
                self.process.stdin.flush()
            except Exception as e:
                self.signals.error.emit(f"Error writing to stdin: {str(e)}")
