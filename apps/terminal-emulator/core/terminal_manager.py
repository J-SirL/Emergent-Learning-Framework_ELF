"""
Terminal Manager - Manages process lifecycle and coordinates with WebBridge
Handles command execution, process management, and communication
"""
import shlex
from PySide6.QtCore import QThreadPool, Qt
from .process_worker import ProcessWorker


class TerminalManager:
    """
    Manages terminal operations and process lifecycle.

    Responsibilities:
    - Parse and execute commands
    - Manage running process workers
    - Route output to the web bridge
    - Handle stdin/stdout/stderr
    """

    def __init__(self, web_bridge):
        """
        Initialize the terminal manager.

        Args:
            web_bridge: WebBridge instance for communication with React
        """
        self.web_bridge = web_bridge
        self.thread_pool = QThreadPool.globalInstance()
        self.current_worker = None

    def run_command(self, command_str):
        """
        Parse and execute a command.

        Args:
            command_str: Command string (e.g., "ping google.com")
        """
        print(f"[TerminalManager] run_command called: {command_str}")

        # Stop any running process
        if self.current_worker:
            print("[TerminalManager] Stopping current worker")
            self.stop_process()

        # Parse command string into arguments
        try:
            command_args = shlex.split(command_str)
            print(f"[TerminalManager] Parsed args: {command_args}")
        except ValueError as e:
            print(f"[TerminalManager] Parse error: {e}")
            self.web_bridge.emit_error(f"Invalid command syntax: {str(e)}")
            return

        if not command_args:
            print("[TerminalManager] No command args, returning")
            return

        # Echo command to terminal
        print(f"[TerminalManager] Echoing command to terminal")
        self.web_bridge.emit_output(f"$ {command_str}", "command")

        # Create and configure worker
        self.current_worker = ProcessWorker(command_args)

        # Connect signals with Qt.QueuedConnection to ensure thread-safe delivery
        self.current_worker.signals.stdout.connect(
            lambda line: self.web_bridge.emit_output(line, "stdout"),
            Qt.ConnectionType.QueuedConnection
        )
        self.current_worker.signals.stderr.connect(
            lambda line: self.web_bridge.emit_output(line, "stderr"),
            Qt.ConnectionType.QueuedConnection
        )
        self.current_worker.signals.finished.connect(
            self._on_process_finished,
            Qt.ConnectionType.QueuedConnection
        )
        self.current_worker.signals.error.connect(
            self.web_bridge.emit_error,
            Qt.ConnectionType.QueuedConnection
        )

        # Start worker in thread pool
        self.thread_pool.start(self.current_worker)

    def send_input(self, data):
        """
        Send input to the running process.

        Args:
            data: String to send to process stdin
        """
        if self.current_worker:
            self.current_worker.write_stdin(data)
            # Echo input to terminal
            self.web_bridge.emit_output(data, "stdin")
        else:
            self.web_bridge.emit_error("No process running")

    def stop_process(self):
        """Stop the currently running process"""
        if self.current_worker:
            self.current_worker.stop()
            self.current_worker = None
            self.web_bridge.emit_output("^C", "system")
            self.web_bridge.emit_finished(-1)

    def _on_process_finished(self, exit_code):
        """
        Handle process completion.

        Args:
            exit_code: Process exit code
        """
        self.current_worker = None
        self.web_bridge.emit_finished(exit_code)

        if exit_code == 0:
            self.web_bridge.emit_output(f"Process exited successfully (code {exit_code})", "system")
        else:
            self.web_bridge.emit_output(f"Process exited with code {exit_code}", "error")
