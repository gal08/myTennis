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
MAX_PENDING_CONNECTIONS = 5


class VideoAudioServer:
    """
    Main server class that:
    - Initializes the network layer
    - Accepts client connections
    - Spawns client handler threads
    - Manages the overall server lifecycle
    """

    def __init__(self, video_path, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.video_path = video_path
        self.network_manager = NetworkManager(host, port)

    def start(self):
        """Starts the server and begins accepting connections."""
        # Initialize network
        self.network_manager.create_server_socket()
        self.network_manager.listen(MAX_PENDING_CONNECTIONS)

        print(f"Video: {self.video_path}")
        print("Waiting for clients...")

        # Main accept loop
        self._accept_clients_loop()

    def _accept_clients_loop(self):
        """Main loop to accept new client connections."""
        while True:
            try:
                client_socket, address = (
                    self.network_manager.accept_connection()
                )
                if client_socket:
                    print(f"Client connected: {address}")

                    # Create handler thread for this client
                    client_thread = threading.Thread(
                        target=self._handle_client_thread,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()

            except Exception as e:
                print(f"Error in client acceptance loop: {e}")
                break

    def _handle_client_thread(self, client_socket, address):
        """Thread function to handle a single client."""
        handler = ClientHandler(self.video_path, client_socket, address)
        handler.handle_streaming()


def run_video_player_server(video_path):
    """Entry point function to start the video streaming server."""
    server = VideoAudioServer(video_path, host=DEFAULT_HOST, port=DEFAULT_PORT)
    server.start()
