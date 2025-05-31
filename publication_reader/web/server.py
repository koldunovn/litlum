"""Simple HTTP server for the publication reader static website."""

import os
import argparse
import http.server
import socketserver
from pathlib import Path
from typing import Optional

from publication_reader.config import Config


def run_server(web_path: Optional[str] = None, port: int = 8080) -> None:
    """Run a simple HTTP server for the static website.
    
    Args:
        web_path: Path to the static website files, uses config if None
        port: Port to run the server on
    """
    # If no web path is provided, use the one from config
    if not web_path:
        config = Config()
        web_path = config.get_web_path()
    
    # Ensure the path exists
    web_path = os.path.expanduser(web_path)
    if not os.path.exists(web_path):
        print(f"Error: Web path {web_path} does not exist")
        print("Make sure you have generated the static website first with:")
        print("python -m publication_reader web")
        return
    
    # Check if index.html exists
    if not os.path.exists(os.path.join(web_path, "index.html")):
        print(f"Warning: No index.html found in {web_path}")
        print("The website may not display correctly")
    
    # Change to the web directory
    os.chdir(web_path)
    
    # Start the server
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    
    print(f"Starting server at http://localhost:{port}")
    print(f"Serving files from {web_path}")
    print("Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a web server for the publication reader")
    parser.add_argument("--path", help="Path to the static website files")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    
    args = parser.parse_args()
    run_server(args.path, args.port)
