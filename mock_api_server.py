"""
Optional mock server for API automation testing.
Serves GET /api/devices/<device_id> with JSON including 'status'.
Uses only Python standard library.
Run: python mock_api_server.py
Then set API_BASE_URL=http://127.0.0.1:8000 (and leave API auth unset) to run api_automation.py.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Mock device store: device_id -> payload
DEVICES = {
    "DEV-001": {"id": "DEV-001", "status": "Active", "model": "CF-100", "serial": "SN001"},
    "DEV-002": {"id": "DEV-002", "status": "Inactive", "model": "CF-100", "serial": "SN002"},
}


class MockAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/devices/"):
            device_id = parsed.path.split("/api/devices/", 1)[-1].split("/")[0]
            if device_id in DEVICES:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(DEVICES[device_id]).encode())
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Device not found", "message": f"No device with id {device_id}"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[Mock API] {args[0]}")


def main():
    server = HTTPServer(("127.0.0.1", 8000), MockAPIHandler)
    print("Mock API server at http://127.0.0.1:8000 (GET /api/devices/<id>)")
    print("Set API_BASE_URL=http://127.0.0.1:8000 and run api_automation.py")
    server.serve_forever()


if __name__ == "__main__":
    main()
