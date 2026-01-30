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
import key_exchange
import aes_cipher

from Protocol import Protocol
from Methods import RequestMethodsHandler
from handle_show_all_stories import run as run_stories_display_server

# Import for video grid display
try:
    from handle_show_all_videos import run as run_videos_display_server
except ImportError:
    run_videos_display_server = None

DEFAULT_HOST = '0.0.0.0'
print("🔥🔥🔥 THIS IS MY SERVER WINDOW 🔥🔥🔥")
DEFAULT_PORT = 5000
MAX_PENDING_CONNECTIONS = 5
SOCKET_REUSE_ADDRESS = 1
SOCK = 0
KEY = 1

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
        self._create_server_socket()

    def start(self):
        """Start the main TCP server."""
        # self._create_server_socket()
        self._print_startup_banner()

        # Start auxiliary servers
        print("[DEBUG] Starting video thumbnail server...")
        self.start_video_thumbnail_server()
        print("[DEBUG] Video thumbnail server started")

        print("[DEBUG] Starting story thumbnail server...")
        self.start_story_thumbnail_server()
        print("[DEBUG] Story thumbnail server started")

        print("[DEBUG] About to start main server loop...")
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
        print("[DEBUG] Server loop started, waiting for connections...")
        while self.running:
            print("[DEBUG] Waiting for client to connect...")
            client_socket, addr = self.server_socket.accept()

            print(f"\n{'=' * 60}")
            print(f"🔌 NEW CLIENT CONNECTED: {addr}")
            print(f"{'=' * 60}\n")

            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket,),
                daemon=True
            )
            client_thread.start()
            print(f"[DEBUG] Started thread for client {addr}")

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
        Handle client connection - DEBUG VERSION
        """
        print(f"\n🔵 [THREAD] handle_client() started")

        conn = (client_socket, None)
        print(f"🔵 [THREAD] Starting key exchange...")
        key = key_exchange.KeyExchange.recv_send_key(conn)
        print("🔵 [THREAD] key =", key, "len =", len(key))
        conn = (client_socket, key)

        try:
            print(f"🔵 [THREAD] Entering request loop...")
            while True:
                print(f"\n{'=' * 60}")
                print(f"🔍 SERVER: Waiting for request...")
                print(f"{'=' * 60}")

                request_data = self._receive_request(conn)
                if not request_data:
                    print(f"❌ No request data received")
                    break

                print(f"📥 Received request:")
                print(f"   Type: {request_data.get('type')}")
                print(f"   Payload: {request_data.get('payload')}")

                # Route request using methods handler
                print(f"\n📡 Routing to methods_handler...")
                response = self.methods_handler.route_request(request_data)

                print(f"✅ Got response from handler:")
                print(f"   {response}")

                # Send response
                print(f"\n📤 Sending response to client...")
                self._send_response(conn, response)
                print(f"✅ Response sent!")
                print(f"{'=' * 60}\n")

        except Exception as e:
            print(f"❌ [ERROR] Client handling: {e}")
            import traceback
            traceback.print_exc()
            self._send_error_response(client_socket, str(e))

        finally:
            client_socket.close()
            print(f"🔌 Client disconnected")

    def _receive_request(self, conn) -> dict:
        """
        Receive and parse client request.

        Args:
            client_socket: Client socket

        Returns:
            Parsed request dictionary or None
        """
        data_raw = Protocol.recv(conn)
        #the decrypt data
        if not data_raw:
            return None

        # Find JSON start
        start_index = data_raw.find(JSON_START_CHAR)
        if start_index == NOT_FOUND_INDEX:
            raise ValueError("Invalid JSON received")

        # Parse JSON
        data_json = data_raw[start_index:].strip()
        return json.loads(data_json)

    def _send_response(self, conn, response: dict):
        """
        Send response to client.

        Args:
            client_socket: Client socket
            response: Response dictionary
        """
        Protocol.send(json.dumps(response), conn)

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