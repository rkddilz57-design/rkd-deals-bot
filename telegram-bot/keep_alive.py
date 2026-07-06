import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer


class _PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"RKD Deals bot is alive")

    def log_message(self, format, *args):
        pass


def _run_server(port):
    server = HTTPServer(("0.0.0.0", port), _PingHandler)
    server.serve_forever()


def _self_ping_loop(url, interval_seconds):
    while True:
        time.sleep(interval_seconds)
        try:
            urllib.request.urlopen(url, timeout=10)
        except Exception as ex:
            print(f"[keep_alive] self-ping failed: {ex}")


def start_keep_alive():
    """Start a tiny HTTP server (for Render's free-tier health checks) and a
    self-ping loop that periodically requests its own public URL so the
    service is not spun down for inactivity. No paid uptime service needed.
    """
    port = int(os.environ.get("PORT", "10000"))
    server_thread = threading.Thread(target=_run_server, args=(port,), daemon=True)
    server_thread.start()
    print(f"[keep_alive] HTTP ping server listening on 0.0.0.0:{port}")

    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    if external_url:
        ping_thread = threading.Thread(
            target=_self_ping_loop, args=(external_url, 600), daemon=True
        )
        ping_thread.start()
        print(f"[keep_alive] self-ping enabled, pinging {external_url} every 10 minutes")
    else:
        print("[keep_alive] RENDER_EXTERNAL_URL not set, self-ping disabled "
              "(this is normal when running locally or outside Render)")
