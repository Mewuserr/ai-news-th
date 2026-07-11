"""Serve the dashboard on the local network so phones on the same WiFi can read it.

Usage: python serve.py [port]
Then on your phone (same WiFi), open: http://<this-pc-LAN-IP>:<port>/index.html
"""
import http.server
import socket
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8787


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    os.chdir(ROOT)
    ip = lan_ip()
    print(f"Serving {ROOT}")
    print(f"On this PC:   http://localhost:{PORT}/index.html")
    print(f"On your phone (same WiFi): http://{ip}:{PORT}/index.html")
    print("Press Ctrl+C to stop.")
    handler = http.server.SimpleHTTPRequestHandler
    with http.server.ThreadingHTTPServer(("0.0.0.0", PORT), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
