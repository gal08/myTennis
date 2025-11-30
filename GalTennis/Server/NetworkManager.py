"""
Gal Haham
Network Manager
Handles all network communication for the streaming server
"""
import socket
import pickle
import struct

NETWORK_LEN_BYTES = 4
REUSE_ADDRESS_ENABLED = 1


class NetworkManager:
    """
    Manages network operations:
    - Socket creation and configuration
    - Sending and receiving data with proper serialization
    - Connection management
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None

    def create_server_socket(self):
        """Creates and configures the server socket."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            REUSE_ADDRESS_ENABLED
        )
        self.server_socket.bind((self.host, self.port))
        return self.server_socket

    def listen(self, max_connections=5):
        """Starts listening for incoming connections."""
        if self.server_socket:
            self.server_socket.listen(max_connections)
            print(f"Server started on {self.host}:{self.port}")

    def accept_connection(self):
        """Accepts a new client connection."""
        if self.server_socket:
            return self.server_socket.accept()
        return None, None

    @staticmethod
    def send_stream_info(client_socket, stream_info):
        """Sends stream metadata to the client."""
        info_data = pickle.dumps(stream_info)
        info_size = struct.pack("!L", len(info_data))
        client_socket.sendall(info_size + info_data)

    @staticmethod
    def send_packet(client_socket, packet):
        """Sends a video/audio packet to the client."""
        packet_data = pickle.dumps(packet)
        packet_size = struct.pack("!L", len(packet_data))
        client_socket.sendall(packet_size + packet_data)

    @staticmethod
    def close_client_socket(client_socket):
        """Closes a client connection."""
        if client_socket:
            client_socket.close()

    def close_server_socket(self):
        """Closes the server socket."""
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
