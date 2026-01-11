"""
Gal Haham
Video & Audio Streaming Server
Main server class that coordinates all components
"""
import threading
from NetworkManager import NetworkManager
from ClientHandler import ClientHandler

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 9999
MAX_PENDING_CONNECTIONS = 1
ACCEPT_TIMEOUT_SECONDS = 30


class VideoAudioServer:
    """
    Main server class that:
    - Initializes the network layer
    - Accepts client connections
    - Spawns client handler threads
    - Manages the overall server lifecycle
    """

    # Class variable to track active server instance
    _active_server = None
    _server_lock = threading.Lock()

    def __init__(self, video_path, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.video_path = video_path
        self.network_manager = NetworkManager(host, port)
        self.is_running = False
        self.client_connected = False

    @classmethod
    def stop_active_server(cls):
        """Stop any currently running server instance"""
        with cls._server_lock:
            if cls._active_server is not None:
                print("[DEBUG] Stopping previous video server...")
                cls._active_server.stop()
                cls._active_server = None

    def start(self):
        """Starts the server and begins accepting connections."""
        # Stop any previous server
        VideoAudioServer.stop_active_server()

        with VideoAudioServer._server_lock:
            VideoAudioServer._active_server = self

        try:
            # Initialize network
            self.network_manager.create_server_socket()
            self.network_manager.listen(MAX_PENDING_CONNECTIONS)
            self.is_running = True

            print(f"Video: {self.video_path}")
            print("Waiting for clients...")

            # Accept ONE client and stream to them
            self._accept_single_client()

        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop()

    def _accept_single_client(self):
        """Accept a single client connection and stream to them."""
        try:
            # Set timeout for accept
            if self.network_manager.server_socket:
                self.network_manager.server_socket.settimeout(
                    ACCEPT_TIMEOUT_SECONDS
                )
            client_socket, address = (
                self.network_manager.accept_connection()
            )

            if client_socket and self.is_running:
                print(f"Client connected: {address}")
                self.client_connected = True

                # Handle this client (blocking until done)
                handler = ClientHandler(
                    self.video_path,
                    client_socket,
                    address
                )
                handler.handle_streaming()

                print(f"Finished streaming to {address}")
                self.client_connected = False

        except Exception as e:
            if self.is_running:
                print(f"Error accepting client: {e}")

    def stop(self):
        """Stop the server and cleanup resources"""
        if self.is_running:
            print("[DEBUG] Shutting down video server...")
            self.is_running = False
            self.network_manager.close_server_socket()
            print("[DEBUG] Video server stopped")


def run_video_player_server(video_path):
    """Entry point function to start the video streaming server."""
    # This will automatically stop any previous server
    server = VideoAudioServer(video_path, host=DEFAULT_HOST, port=DEFAULT_PORT)
    server.start()
