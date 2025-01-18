from http.server import HTTPServer, BaseHTTPRequestHandler
from queue import Queue
import threading

class OAuthRedirectHandler(BaseHTTPRequestHandler):
    """Handles OAuth redirects."""
    def do_GET(self):
        # Ignore requests for /favicon.ico
        if self.path == "/favicon.ico":
            self.send_response(404)  # Respond with "Not Found"
            self.end_headers()
            return

        # Send the authorization response back to the queue
        self.server.queue.put(self.path)  # Use the queue to share data
        print(f"Received auth_response: {self.path}")

        # Send a success response to the browser
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Authentication successful! You can close this window.")

def start_local_server(port=8081, queue=None):
    """Starts a local server to handle OAuth redirects."""
    print(f"Starting local server on http://localhost:{port}")
    server = HTTPServer(('localhost', port), OAuthRedirectHandler)
    server.queue = queue  # Attach the queue to the server
    thread = threading.Thread(target=server.serve_forever)
    thread.setDaemon(True)
    thread.start()
    return server