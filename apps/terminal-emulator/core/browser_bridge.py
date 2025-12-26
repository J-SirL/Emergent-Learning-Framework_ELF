"""
Browser Bridge - Intercepts browser open requests and routes to our app
This script is set as the BROWSER environment variable
"""
import sys
import socket
import json

# Port for URL notifications (same as PTY server + 1)
DEFAULT_PORT = 8766


def send_url(url: str, port: int = None):
    """Send URL to the main app via UDP"""
    if port is None:
        # Try to read port from env or use default
        import os
        port = int(os.environ.get('BROWSER_BRIDGE_PORT', DEFAULT_PORT))

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = json.dumps({'type': 'open_url', 'url': url})
        sock.sendto(message.encode(), ('127.0.0.1', port))
        sock.close()
        print(f"[browser-bridge] Sent URL to app: {url}")
        return True
    except Exception as e:
        print(f"[browser-bridge] Failed to send URL: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: browser_bridge.py <url>")
        sys.exit(1)

    url = sys.argv[1]

    # Handle common URL formats
    if not url.startswith(('http://', 'https://', 'file://')):
        url = 'https://' + url

    success = send_url(url)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
