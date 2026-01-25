"""
Gal Haham
Main Tennis Social server application.
Routes client requests, manages handlers, and coordinates
video/story streaming servers.
REFACTORED: Constants extracted, methods split, brief docs.
ENHANCED: Auto-starts thumbnail servers on startup!
SIMPLIFIED: Business logic extracted to methods.py
"""
import socket
import json
import threading
import time
import os

from Protocol import Protocol
from Methods import RequestMethodsHandler
from handle_show_all_stories import run as run_stories_display_server

# Import for video grid display
try:
    from handle_show_all_videos import run as run_videos_display_server
except ImportError:
    run_videos_display_server = None

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000
MAX_PENDING_CONNECTIONS = 5
SOCKET_REUSE_ADDRESS = 1

VIDEO_FOLDER = "videos"
STORY_FOLDER = "stories"

HALF_SECOND = 0.5
SEPARATOR_LENGTH = 50
SEPARATOR_CHAR = "="

JSON_START_CHAR = '{'
NOT_FOUND_INDEX = -1

KEY_TYPE = 'type'
KEY_PAYLOAD = 'payload'
KEY_STATUS = 'status'
KEY_MESSAGE = 'message'


class Server:
    """Main Tennis Social server - simplified to focus on networking."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        """
        Initialize server.

        Args:
            host: Server hostname
            port: Server port
        """
        self.host = host
        self.port = port
        self.running = False
        self.video_thumbnail_server_running = False
        self.story_thumbnail_server_running = False

        # Initialize the methods handler (contains all business logic)
        self.methods_handler = RequestMethodsHandler()

        # Ensure folders
        os.makedirs(VIDEO_FOLDER, exist_ok=True)
        os.makedirs(STORY_FOLDER, exist_ok=True)

    def start(self):
        """Start the main TCP server."""
        self._create_server_socket()
        self._print_startup_banner()

        # Start auxiliary servers
        self.start_video_thumbnail_server()
        self.start_story_thumbnail_server()

        try:
            self._run_server_loop()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"Server error: {e}")
            self.stop()

    def _create_server_socket(self):
        """Create and configure server socket."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            SOCKET_REUSE_ADDRESS
        )
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MAX_PENDING_CONNECTIONS)
        self.running = True

    def _print_startup_banner(self):
        """Print server startup information."""
        separator = SEPARATOR_CHAR * SEPARATOR_LENGTH
        print(separator)
        print("Tennis Social Server")
        print(separator)
        print(f"Main Server: {self.host}:{self.port}")
        print(separator)
        print("Server is ready and waiting for clients...")
        print(separator)

    def _run_server_loop(self):
        """Main server loop - accept and handle clients."""
        while self.running:
            client_socket, addr = self.server_socket.accept()

            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket,),
                daemon=True
            )
            client_thread.start()

    def stop(self):
        """Stop the server."""
        self.running = False
        self.server_socket.close()
        print("\nServer stopped.")

    def start_video_thumbnail_server(self):
        """Start video thumbnail server (port 2223) automatically."""
        if not self.video_thumbnail_server_running:
            def run_video_thumb_server():
                try:
                    print("Starting Video Thumbnail Server (port 2223)...")
                    if run_videos_display_server:
                        run_videos_display_server()
                    else:
                        print("[WARN] Video thumbnail server not available")
                except Exception as e:
                    print(f"[ERROR] Video thumbnail server: {e}")
                    import traceback
                    traceback.print_exc()

            thread = threading.Thread(
                target=run_video_thumb_server,
                daemon=True
            )
            thread.start()
            self.video_thumbnail_server_running = True
            time.sleep(HALF_SECOND)

    def start_story_thumbnail_server(self):
        """Start story thumbnail server (port 2222) automatically."""
        if not self.story_thumbnail_server_running:
            def run_story_thumb_server():
                try:
                    print("Starting Story Thumbnail Server (port 2222)...")
                    run_stories_display_server()
                except Exception as e:
                    print(f"[ERROR] Story thumbnail server: {e}")
                    import traceback
                    traceback.print_exc()

            thread = threading.Thread(
                target=run_story_thumb_server,
                daemon=True
            )
            thread.start()
            self.story_thumbnail_server_running = True
            time.sleep(HALF_SECOND)

    def handle_client(self, client_socket: socket.socket):
        """
        Handle client connection.

        Args:
            client_socket: Client socket connection
        """
        try:
            while True:
                request_data = self._receive_request(client_socket)
                if not request_data:
                    break

                # Route request using methods handler
                response = self.methods_handler.route_request(request_data)

                # Send response
                self._send_response(client_socket, response)

        except Exception as e:
            print(f"[ERROR] Client handling: {e}")
            self._send_error_response(client_socket, str(e))

        finally:
            client_socket.close()

    def _receive_request(self, client_socket: socket.socket) -> dict:
        """
        Receive and parse client request.

        Args:
            client_socket: Client socket

        Returns:
            Parsed request dictionary or None
        """
        data_raw = Protocol.recv(client_socket)
        if not data_raw:
            return None

        # Find JSON start
        start_index = data_raw.find(JSON_START_CHAR)
        if start_index == NOT_FOUND_INDEX:
            raise ValueError("Invalid JSON received")

        # Parse JSON
        data_json = data_raw[start_index:].strip()
        return json.loads(data_json)

    def _send_response(self, client_socket: socket.socket, response: dict):
        """
        Send response to client.

        Args:
            client_socket: Client socket
            response: Response dictionary
        """
        Protocol.send(client_socket, json.dumps(response))

    def _send_error_response(self, client_socket: socket.socket, error: str):
        """
        Send error response to client.

        Args:
            client_socket: Client socket
            error: Error message
        """
        try:
            Protocol.send(
                client_socket,
                json.dumps({KEY_STATUS: "error", KEY_MESSAGE: error})
            )
        except:
            pass


if __name__ == '__main__':
    server_app = Server()
    server_app.start()