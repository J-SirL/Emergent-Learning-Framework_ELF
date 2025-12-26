"""
PTY WebSocket Server - Bridges xterm.js to ConPTY via pywinpty
"""
import asyncio
import json
import os
import shutil
import signal
import sys
from pathlib import Path

# Add websockets to requirements
try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

try:
    import winpty
except ImportError:
    print("Installing pywinpty...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywinpty"])
    import winpty


class PTYSession:
    """Manages a single PTY session"""

    def __init__(self, cols: int = 120, rows: int = 30, browser_bridge_port: int = None):
        self.cols = cols
        self.rows = rows
        self.pty = None
        self.running = False
        self.browser_bridge_port = browser_bridge_port

    def spawn(self, command: str = None, cwd: str = None):
        """Spawn a PTY process"""
        self.pty = winpty.PTY(cols=self.cols, rows=self.rows)

        # Set up environment with browser bridge
        env = os.environ.copy()
        if self.browser_bridge_port:
            # Point BROWSER to our bridge script
            bridge_script = Path(__file__).parent / "browser_bridge.py"
            python_exe = sys.executable
            env['BROWSER'] = f'"{python_exe}" "{bridge_script}"'
            env['BROWSER_BRIDGE_PORT'] = str(self.browser_bridge_port)

        if command:
            # Parse command
            parts = command.split(None, 1)
            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else None

            # Find executable
            exe = shutil.which(cmd) or shutil.which(cmd + ".exe")
            if not exe:
                # Fallback to cmd /c
                exe = shutil.which("cmd.exe")
                args = f"/c {command}"
        else:
            # Default: spawn shell
            exe = os.environ.get("COMSPEC", "cmd.exe")
            args = None

        if not exe:
            raise RuntimeError(f"Could not find executable: {command or 'shell'}")

        cwd = cwd or str(Path.home())

        if not self.pty.spawn(appname=exe, cmdline=args, cwd=cwd):
            raise RuntimeError(f"Failed to spawn PTY: {exe} {args}")

        self.running = True
        return True

    def read(self) -> str | None:
        """Non-blocking read from PTY"""
        if not self.pty or not self.running:
            return None
        try:
            data = self.pty.read(blocking=False)
            return data if data else None
        except Exception:
            return None

    def write(self, data: str):
        """Write to PTY"""
        if self.pty and self.running:
            try:
                self.pty.write(data)
            except Exception as e:
                print(f"PTY write error: {e}")

    def resize(self, cols: int, rows: int):
        """Resize PTY"""
        if self.pty:
            try:
                self.pty.set_size(cols, rows)
                self.cols = cols
                self.rows = rows
            except Exception:
                pass

    def is_alive(self) -> bool:
        """Check if PTY is still running"""
        if not self.pty:
            return False
        try:
            return self.pty.isalive()
        except Exception:
            return False

    def close(self):
        """Close PTY session"""
        self.running = False
        # PTY will be garbage collected


class PTYWebSocketServer:
    """WebSocket server that bridges xterm.js to PTY"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765, url_callback=None,
                 startup_command: str = None, startup_input: str = None):
        self.host = host
        self.port = port
        self.url_callback = url_callback  # Called when URL received from browser bridge
        self.startup_command = startup_command  # Command to spawn (e.g., "claude")
        self.startup_input = startup_input  # Input to send after spawn (e.g., "checkin\n")
        self.sessions: dict[websockets.WebSocketServerProtocol, PTYSession] = {}
        self.active_websockets: list = []  # For broadcasting URL messages

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        """Handle a WebSocket connection"""
        print(f"Client connected: {websocket.remote_address}")
        self.active_websockets.append(websocket)

        # Create PTY session with browser bridge port (UDP is on port + 1)
        session = PTYSession(browser_bridge_port=self.port + 1)
        self.sessions[websocket] = session

        try:
            # Spawn shell or custom command
            session.spawn(command=self.startup_command)
            print(f"PTY spawned successfully{' with: ' + self.startup_command if self.startup_command else ''}")

            # Start read loop
            read_task = asyncio.create_task(self.read_loop(websocket, session))

            # Send startup input after a brief delay (e.g., auto-checkin)
            if self.startup_input:
                async def send_startup():
                    await asyncio.sleep(2.0)  # Wait for shell/claude to initialize
                    session.write(self.startup_input)
                    print(f"Sent startup input: {repr(self.startup_input)}")
                asyncio.create_task(send_startup())

            # Handle incoming messages
            async for message in websocket:
                await self.handle_message(websocket, session, message)

        except Exception as e:
            print(f"Session error: {e}")
            try:
                await websocket.send(f"\r\n\x1b[31mError: {e}\x1b[0m\r\n")
            except Exception:
                pass

        finally:
            # Cleanup
            print(f"Client disconnected: {websocket.remote_address}")
            session.close()
            del self.sessions[websocket]
            if websocket in self.active_websockets:
                self.active_websockets.remove(websocket)
            read_task.cancel()

    async def broadcast_url(self, url: str):
        """Send URL to all connected clients"""
        message = json.dumps({'type': 'open_url', 'url': url})
        for ws in self.active_websockets:
            try:
                await ws.send(message)
            except Exception:
                pass
        # Also call callback if set
        if self.url_callback:
            self.url_callback(url)

    async def read_loop(self, websocket: websockets.WebSocketServerProtocol, session: PTYSession):
        """Continuously read from PTY and send to WebSocket"""
        try:
            while session.is_alive():
                data = session.read()
                if data:
                    # Batch multiple reads if available
                    for _ in range(10):  # Try to batch up to 10 reads
                        more = session.read()
                        if more:
                            data += more
                        else:
                            break
                    try:
                        await websocket.send(data)
                    except Exception:
                        break
                    await asyncio.sleep(0.005)  # 5ms after data
                else:
                    await asyncio.sleep(0.016)  # ~60fps poll when idle

            # PTY exited
            try:
                await websocket.send("\r\n\x1b[33m[Process exited]\x1b[0m\r\n")
            except Exception:
                pass

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Read loop error: {e}")

    async def handle_message(self, websocket, session: PTYSession, message: str):
        """Handle incoming WebSocket message"""
        try:
            msg = json.loads(message)
            msg_type = msg.get("type")

            if msg_type == "input":
                # User input
                data = msg.get("data", "")
                session.write(data)

            elif msg_type == "resize":
                # Terminal resize
                cols = msg.get("cols", 120)
                rows = msg.get("rows", 30)
                session.resize(cols, rows)

            elif msg_type == "command":
                # Spawn new command (restart PTY)
                command = msg.get("command")
                cwd = msg.get("cwd")
                session.close()
                session.spawn(command=command, cwd=cwd)

        except json.JSONDecodeError:
            # Raw input (fallback)
            session.write(message)
        except Exception as e:
            print(f"Message handling error: {e}")

    async def start(self):
        """Start the WebSocket server"""
        print(f"Starting PTY WebSocket server on ws://{self.host}:{self.port}")

        # Start UDP listener for browser bridge (on port + 1 to avoid conflict)
        udp_port = self.port + 1
        asyncio.create_task(self.udp_listener_task(udp_port))

        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        ):
            print("Server running. Press Ctrl+C to stop.")
            await asyncio.Future()  # Run forever

    async def udp_listener_task(self, port: int):
        """Listen for URL messages from browser bridge via UDP"""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.bind((self.host, port))
        print(f"Browser bridge UDP listener on {self.host}:{port}")

        loop = asyncio.get_event_loop()
        while True:
            try:
                data = await loop.sock_recv(sock, 4096)
                if data:
                    try:
                        msg = json.loads(data.decode())
                        if msg.get('type') == 'open_url':
                            url = msg.get('url')
                            print(f"[browser-bridge] Received URL: {url}")
                            await self.broadcast_url(url)
                    except json.JSONDecodeError:
                        pass
            except Exception:
                await asyncio.sleep(0.1)

    def run(self):
        """Run the server (blocking)"""
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            print("\nServer stopped.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PTY WebSocket Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    args = parser.parse_args()

    server = PTYWebSocketServer(host=args.host, port=args.port)
    server.run()


if __name__ == "__main__":
    main()
