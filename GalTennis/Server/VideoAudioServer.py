"""
Gal Haham
Video & Audio Streaming Server - ENCRYPTED VERSION
Main server class that coordinates all components
ENHANCED: Added full encryption support via Diffie-Hellman + AES
FIXED: Now supports MULTIPLE concurrent clients
"""
import threading
import socket
import key_exchange
from NetworkManager import NetworkManager
from ClientHandler import ClientHandler

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 9999
MAX_PENDING_CONNECTIONS = 10
ACCEPT_TIMEOUT_SECONDS = 30
MAX_CONCURRENT_STREAMS = 10


class VideoAudioServer:
    """
    Main server class that:
    - Initializes the network layer
    - Accepts MULTIPLE client connections with encryption
    - Spawns client handler threads for each client
    - Manages the overall server lifecycle
    """

    _active_servers = []
    _server_lock = threading.Lock()

    def __init__(self, video_path, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.video_path = video_path
        self.network_manager = NetworkManager(host, port)
        self.is_running = False
        self.active_clients = []
        self.client_lock = threading.Lock()

    @classmethod
    def cleanup_finished_servers(cls):
        """Remove finished server instances from tracking"""
        with cls._server_lock:
            cls._active_servers = [
                s for s in cls._active_servers if s.is_running
            ]

    def start(self):
        """Starts the server and begins accepting MULTIPLE connections."""
        with VideoAudioServer._server_lock:
            VideoAudioServer._active_servers.append(self)

        try:
            self.network_manager.create_server_socket()
            self.network_manager.listen(MAX_PENDING_CONNECTIONS)
            self.is_running = True

            print(f"Encrypted Video Server Started")
            print(f"Video: {self.video_path}")

            self._accept_multiple_clients()

        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop()

    def _accept_multiple_clients(self):
        """Accept MULTIPLE client connections - each in its own thread."""
        client_counter = 0

        while self.is_running:
            try:
                if self.network_manager.server_socket:
                    self.network_manager.server_socket.settimeout(
                        ACCEPT_TIMEOUT_SECONDS
                    )

                client_socket, address = (
                    self.network_manager.accept_connection()
                )

                if client_socket and self.is_running:
                    with self.client_lock:
                        if len(self.active_clients) >= MAX_CONCURRENT_STREAMS:
                            client_socket.close()
                            continue

                    client_counter += 1
                    print(f"Client #{client_counter} connected: {address}")

                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address, client_counter),
                        daemon=True,
                        name=f"ClientHandler-{client_counter}"
                    )
                    client_thread.start()

            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    print(f"Error accepting client: {e}")
                    import traceback
                    traceback.print_exc()

    def _handle_client(self, client_socket, address, client_number):
        """Handle a single client connection with encryption."""
        try:
            with self.client_lock:
                self.active_clients.append(address)

            conn = (client_socket, None)
            encryption_key = key_exchange.KeyExchange.recv_send_key(conn)
            encrypted_conn = (client_socket, encryption_key)
            print(
                f"[Client #{client_number}] Encryption established "
                f"({len(encryption_key)} bytes)"
            )
            handler = ClientHandler(
                self.video_path,
                encrypted_conn,
                address
            )
            handler.handle_streaming()

            print(f"[Client #{client_number}] Finished streaming to {address}")

        except Exception as e:
            print(f"[Client #{client_number}] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            with self.client_lock:
                if address in self.active_clients:
                    self.active_clients.remove(address)
                remaining = len(self.active_clients)

            print(
                f"[Client #{client_number}] Disconnected. "
                f"Active clients: {remaining}/{MAX_CONCURRENT_STREAMS}"
            )
            try:
                client_socket.close()
            except:
                pass

    def stop(self):
        """Stop the server and cleanup resources"""
        if self.is_running:
            print("[DEBUG] Shutting down video server...")
            self.is_running = False
            self.network_manager.close_server_socket()

            with VideoAudioServer._server_lock:
                if self in VideoAudioServer._active_servers:
                    VideoAudioServer._active_servers.remove(self)

            print("[DEBUG] Video server stopped")


def run_video_player_server(video_path):
    """Entry point function to start the video streaming server."""
    server = VideoAudioServer(video_path, host=DEFAULT_HOST, port=DEFAULT_PORT)
    server.start()
