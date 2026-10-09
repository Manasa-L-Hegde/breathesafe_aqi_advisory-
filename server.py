"""
server.py — Local Development Server for BreatheSafe

Serves the BreatheSafe interactive dashboard at http://localhost:8000/
and emulates the AWS API Gateway endpoint at /api so you can test
both static mock mode and live Lambda routing completely offline.

Usage:
    python server.py
    # or specify a custom port:
    python server.py 8080
"""

import http.server
import socketserver
import urllib.parse
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")

# Import Lambda handler for local /api emulation
try:
    import lambda_function
    HAS_LAMBDA = True
except Exception as err:
    HAS_LAMBDA = False
    print(f"[BreatheSafe Server] Note: Lambda handler not available ({err})")


class BreatheSafeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.end_headers()

    def do_GET(self):
        """Serve static dashboard or route API requests to Lambda handler."""
        parsed = urllib.parse.urlparse(self.path)

        # Route /api or /forecast to the local AWS Lambda simulation
        if parsed.path in ("/api", "/api/", "/forecast", "/forecast/"):
            if HAS_LAMBDA:
                query_params = dict(urllib.parse.parse_qsl(parsed.query))
                event = {
                    "httpMethod": "GET",
                    "queryStringParameters": query_params,
                    "rawQueryString": parsed.query,
                }
                response = lambda_function.lambda_handler(event, None)
                status_code = response.get("statusCode", 200)
                body = response.get("body", "{}")
                headers = response.get("headers", {})

                self.send_response(status_code)
                for header_name, header_value in headers.items():
                    self.send_header(header_name, header_value)
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))
                return
            else:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Lambda handler not loaded"}).encode("utf-8"))
                return

        # Otherwise serve static assets from dashboard/
        return super().do_GET()


def run_server(port=8000):
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), BreatheSafeHandler) as httpd:
        print("=================================================================")
        print("  BreatheSafe — Local Development Server")
        print("=================================================================")
        print(f"  Dashboard: http://localhost:{port}/")
        print(f"  Local API: http://localhost:{port}/api")
        print("  Press Ctrl+C to stop the server.")
        print("=================================================================")
        sys.stdout.flush()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down BreatheSafe server.")


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
