"""
Gal Haham
Video & Audio Streaming Server
Main server class that coordinates all components
ENHANCED: Added full encryption support via Diffie-Hellman + AES
FIXED: Now supports MULTIPLE concurrent clients
FIXED: Direct socket communication without NetworkManager dependency
"""
import threading
import socket
import pickle
import struct
import key_exchange
import aes_cipher
from ClientHandler import ClientHandler

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 9999
MAX_PENDING_CONNECTIONS = 10
ACCEPT_TIMEOUT_SECONDS = 30
MAX_CONCURRENT_STREAMS = 10
SOCKET_REUSE_ADDRESS = 1
STRUCT_FORMAT_LONG = "!L"


class VideoAudioServer:

    _active_servers = []
    _server_lock = threading.Lock()

    def __init__(self, video_path, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.video_path = video_path
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.active_clients = []
        self.client_lock = threading.Lock()

    @classmethod
    def cleanup_finished_servers(cls):
        with cls._server_lock:
            cls._active_servers = [
                s for s in cls._active_servers if s.is_running
            ]

    def start(self):
        with VideoAudioServer._server_lock:
            VideoAudioServer._active_servers.append(self)

        try:
            self._create_server_socket()
            self.is_running = True

            print(f"Encrypted Video Server Started")
            print(f"Video: {self.video_path}")
            print(f"Listening on {self.host}:{self.port}")

            self._accept_multiple_clients()

        except Exception as e:
            print(f"Server error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()

    def _create_server_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            SOCKET_REUSE_ADDRESS
        )
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MAX_PENDING_CONNECTIONS)

    def _accept_multiple_clients(self):
        client_counter = 0

        while self.is_running:
            try:
                if self.server_socket:
                    self.server_socket.settimeout(ACCEPT_TIMEOUT_SECONDS)

                client_socket, address = self.server_socket.accept()

                if client_socket and self.is_running:
                    with self.client_lock:
                        if len(self.active_clients) >= MAX_CONCURRENT_STREAMS:
                            print(
                                f"[DEBUG] Max concurrent streams reached, "
                                f"rejecting client {address}"
                            )
                            client_socket.close()
                            continue

                    client_counter += 1
                    print(
                        f"[DEBUG] Client #{client_counter} connected from "
                        f"{address}"
                    )

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
                    print(f"[DEBUG] Error accepting client: {e}")
                    import traceback
                    traceback.print_exc()

    def _handle_client(self, client_socket, address, client_number):
        try:
            with self.client_lock:
                self.active_clients.append(address)

            print(
                f"[Client #{client_number}] Starting key exchange with "
                f"{address}..."
            )

            conn = (client_socket, None)
            encryption_key = key_exchange.KeyExchange.recv_send_key(conn)
            encrypted_conn = (client_socket, encryption_key)

            print(
                f"[Client #{client_number}] Encryption established "
                f"({len(encryption_key)} bytes)"
            )

            print(f"[Client #{client_number}] Creating ClientHandler...")
            handler = ClientHandler(
                self.video_path,
                encrypted_conn,
                address,
                client_number
            )

            print(
                f"[Client #{client_number}] Starting streaming with "
                f"stream info..."
            )
            handler.handle_streaming()

            print(
                f"[Client #{client_number}] Finished streaming to {address}"
            )

        except Exception as e:
            print(f"[Client #{client_number}] Error during streaming: {e}")
            import traceback
            traceback.print_exc()
        finally:
            with self.client_lock:
                if address in self.active_clients:
                    self.active_clients.remove(address)
                remaining = len(self.active_clients)

            print(
                f"[Client #{client_number}] Disconnected from {address}. "
                f"Active clients: {remaining}/{MAX_CONCURRENT_STREAMS}"
            )
            try:
                client_socket.close()
            except Exception as e:
                print(f"[Client #{client_number}] Error closing socket: {e}")

    def stop(self):
        if self.is_running:
            print("[DEBUG] Shutting down video server...")
            self.is_running = False

            if self.server_socket:
                try:
                    self.server_socket.close()
                except Exception as e:
                    print(f"[DEBUG] Error closing server socket: {e}")
                self.server_socket = None

            with VideoAudioServer._server_lock:
                if self in VideoAudioServer._active_servers:
                    VideoAudioServer._active_servers.remove(self)

            print("[DEBUG] Video server stopped")


def run_video_player_server(video_path):
    server = VideoAudioServer(video_path, host=DEFAULT_HOST, port=DEFAULT_PORT)
    server.start()
