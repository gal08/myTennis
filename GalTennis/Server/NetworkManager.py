"""
Gal Haham
Network Manager - Handles all network communication for the streaming server.
REFACTORED: Added missing constants, brief documentation.
"""
import socket
import pickle
import struct

NETWORK_LEN_BYTES = 4
REUSE_ADDRESS_ENABLED = 1
DEFAULT_MAX_CONNECTIONS = 5
STRUCT_FORMAT_LONG = "!L"


class NetworkManager:
    """
    Manages network operations:
    - Socket creation and configuration
    - Sending and receiving data with proper serialization
    - Connection management
    """

    def __init__(self, host: str, port: int):
        """
        Initialize network manager.

        Args:
            host: Server hostname/IP
            port: Server port
        """
        self.host = host
        self.port = port
        self.server_socket = None

    def create_server_socket(self) -> socket.socket:
        """
        Create and configure server socket.

        Returns:
            Configured server socket
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            REUSE_ADDRESS_ENABLED
        )
        self.server_socket.bind((self.host, self.port))
        return self.server_socket

    def listen(self, max_connections: int = DEFAULT_MAX_CONNECTIONS):
        """
        Start listening for connections.

        Args:
            max_connections: Maximum pending connections
        """
        if self.server_socket:
            self.server_socket.listen(max_connections)
            print(f"Server started on {self.host}: {self.port}")

    def accept_connection(self):
        """
        Accept new client connection.

        Returns:
            Tuple of (client_socket, address) or (None, None)
        """
        if self.server_socket:
            return self.server_socket.accept()
        return None, None

    @staticmethod
    def send_stream_info(client_socket: socket.socket, stream_info: dict):
        """
        Send stream metadata to client.

        Args:
            client_socket: Client socket
            stream_info: Stream metadata dictionary
        """
        info_data = pickle.dumps(stream_info)
        info_size = struct.pack(STRUCT_FORMAT_LONG, len(info_data))
        client_socket.sendall(info_size + info_data)

    @staticmethod
    def send_packet(client_socket: socket.socket, packet: dict):
        """
        Send video/audio packet to client.

        Args:
            client_socket: Client socket
            packet: Packet data dictionary
        """
        packet_data = pickle.dumps(packet)
        packet_size = struct.pack(STRUCT_FORMAT_LONG, len(packet_data))
        client_socket.sendall(packet_size + packet_data)

    @staticmethod
    def close_client_socket(client_socket: socket.socket):
        """
        Close client connection.

        Args:
            client_socket: Client socket to close
        """
        if client_socket:
            client_socket.close()

    def close_server_socket(self):
        """Close server socket."""
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
