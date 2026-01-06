#!/usr/bin/env python3
"""
Simple proxy server for the Bitcoin Monitor.
Serves static files and proxies Polymarket API requests to avoid CORS issues.
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import json
import os
from urllib.parse import urlparse, parse_qs

PORT = 8080

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Proxy Polymarket Gamma API
        if self.path.startswith('/api/gamma/'):
            self.proxy_request('https://gamma-api.polymarket.com' + self.path[10:])
            return

        # Proxy Polymarket CLOB API
        if self.path.startswith('/api/clob/'):
            self.proxy_request('https://clob.polymarket.com' + self.path[9:])
            return

        # Serve static files normally
        return super().do_GET()

    def proxy_request(self, url):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            req.add_header('Accept', 'application/json')

            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', len(data))
                self.end_headers()
                self.wfile.write(data)

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def log_message(self, format, *args):
        # Custom logging
        if '/api/' in args[0]:
            print(f"[PROXY] {args[0]}")
        else:
            pass  # Suppress static file logs

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        print(f"Bitcoin Monitor running at http://localhost:{PORT}")
        print("Proxying Polymarket APIs to avoid CORS issues")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
