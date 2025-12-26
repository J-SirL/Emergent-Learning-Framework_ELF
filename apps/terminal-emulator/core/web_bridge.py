"""
Web Bridge - QWebChannel bridge for Python ↔ JavaScript communication
Exposes Python methods to React and emits signals for real-time updates
"""
from PySide6.QtCore import QObject, Signal, Slot, Property


class WebBridge(QObject):
    """
    Bridge object exposed to JavaScript via QWebChannel.

    JavaScript can call Python methods:
        bridge.runCommand("ping google.com");
        bridge.sendInput("hello");
        bridge.stopProcess();

    Python can emit signals to JavaScript:
        bridge.outputReceived.emit("Hello from Python");
    """

    # Signals (Python → JavaScript)
    # IMPORTANT: QWebChannel signals must use basic types (str, int, bool, float)
    testSignal = Signal()  # Test signal with no parameters
    outputReceived = Signal(str, str)  # (line, type) where type is 'stdout' or 'stderr'
    processFinished = Signal(int)  # Exit code
    processError = Signal(str)  # Error message
    leaderboardUpdated = Signal(str)  # JSON string of leaderboard data
    authStatusChanged = Signal(bool, str)  # (isAuthenticated, username)

    def __init__(self, terminal_manager):
        """
        Initialize the web bridge.

        Args:
            terminal_manager: TerminalManager instance
        """
        super().__init__()
        self.terminal_manager = terminal_manager
        self._is_authenticated = False
        self._username = ""
        print(f"[WebBridge] __init__: Signals defined: outputReceived={self.outputReceived}, processFinished={self.processFinished}")

    @Slot(str)
    def runCommand(self, command):
        """
        Run a command in the terminal (called from JavaScript).

        Args:
            command: Command string to execute
        """
        print(f"[Bridge] runCommand called with: {command}")
        self.terminal_manager.run_command(command)

    @Slot(str)
    def sendInput(self, data):
        """
        Send input to running process stdin (called from JavaScript).

        Args:
            data: String to send to stdin
        """
        self.terminal_manager.send_input(data)

    @Slot()
    def stopProcess(self):
        """Stop the currently running process (called from JavaScript)"""
        self.terminal_manager.stop_process()

    @Slot(str, int)
    def submitScore(self, username, score):
        """
        Submit a score to the leaderboard (called from JavaScript).

        Args:
            username: GitHub username
            score: Score to submit
        """
        # This will be implemented in the GitHub API utility
        print(f"Submitting score: {username} - {score}")

    @Slot(str)
    def authenticateGitHub(self, access_token):
        """
        Authenticate user with GitHub access token (called from JavaScript).

        Args:
            access_token: GitHub OAuth access token
        """
        # Store token and fetch user info
        # This will be implemented with the GitHub API utility
        self._is_authenticated = True
        self._username = "GitHubUser"  # Placeholder
        self.authStatusChanged.emit(True, self._username)

    @Slot()
    def logout(self):
        """Logout from GitHub (called from JavaScript)"""
        self._is_authenticated = False
        self._username = ""
        self.authStatusChanged.emit(False, "")

    @Slot(result=bool)
    def isAuthenticated(self):
        """Check if user is authenticated (called from JavaScript)"""
        return self._is_authenticated

    @Slot(result=str)
    def getUsername(self):
        """Get current username (called from JavaScript)"""
        return self._username

    @Slot(result=str)
    def getVersion(self):
        """Get app version (called from JavaScript)"""
        from config import Config
        return Config.APP_VERSION

    # Python-side methods for emitting signals
    def emit_output(self, line, output_type):
        """Emit output to JavaScript"""
        print(f"[WebBridge] emit_output: type={output_type}, line={line[:100]}")
        self.outputReceived.emit(line, output_type)

    def emit_finished(self, exit_code):
        """Emit process finished signal"""
        print(f"[WebBridge] emit_finished: exit_code={exit_code}")
        self.processFinished.emit(exit_code)

    def emit_error(self, error_msg):
        """Emit error signal"""
        print(f"[WebBridge] emit_error: {error_msg}")
        self.processError.emit(error_msg)

    def emit_leaderboard(self, leaderboard_json):
        """Emit leaderboard update"""
        self.leaderboardUpdated.emit(leaderboard_json)
