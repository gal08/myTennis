"""
Gal Haham
Media file uploader client - ENCRYPTED VERSION
Converts images/videos to Base64 and sends them to the media server via TCP
ENHANCED: Added full encryption support via Diffie-Hellman + AES
"""
import socket
import base64
import json
import struct
import os
from pathlib import Path
import key_exchange
import aes_cipher


# Network Configuration
HOST = "127.0.0.1"
PORT = 3333
MSG_LEN = 1024

# Protocol
PAYLOAD_SIZE_BYTES = 4
PAYLOAD_SIZE_FORMAT = "!I"

# File Types
VIDEO_EXTENSION = ".mp4"
MEDIA_TYPE_VIDEO = "video"
MEDIA_TYPE_IMAGE = "image"

# File Mode
FILE_MODE_READ_BINARY = "rb"

# Default Values
DEFAULT_USERNAME = "user"

# Error Messages
ERROR_FILE_NOT_FOUND = "file not found"

SOCK_INDEX = 0
KEY_INDEX = 1


class MediaClient:
    """
    MediaClient sends image/video files to a remote server with ENCRYPTION.

    Responsibilities:
    - Load a media file (image or mp4).
    - Convert file to Base64 encoded string.
    - Build a JSON payload containing file + metadata.
    - ðŸ”’ ENCRYPT the payload with AES-256
    - Send encrypted payload to server
    - Read a short server response.
    """

    def __init__(self, host=HOST, port=PORT):
        """
        Initialize the media client.

        Args:
            host: Server hostname/IP address
            port: Server port number
        """
        self.host = host
        self.port = port

    def send_media(self, file_path, username=DEFAULT_USERNAME):
        """
        Send a media file (image or video) to the server with ENCRYPTION.

        Steps performed:
        1. Verifies that the file exists.
        2. Reads the file as raw bytes.
        3. Converts the file into Base64 so it can be sent as text.
        4. Detects whether the file is an image or a video based on extension.
        5. Builds a JSON payload
        6. ðŸ”’ Establishes encrypted connection
        7. ðŸ”’ Encrypts the payload with AES
        8. Sends the size of the encrypted payload and then the payload itself
        9. Waits for a short response from the server and prints it.

        Args:
            file_path: Path to media file (image or video)
            username: Username to associate with the upload

        Raises:
            FileNotFoundError: If file does not exist
        """
        # Load and encode file
        file_bytes = self._load_file(file_path)
        b64_data = self._encode_to_base64(file_bytes)

        # Detect media type and build payload
        media_type = self._detect_media_type(file_path)
        payload_bytes = self._build_payload(username, media_type, b64_data)

        # Send to server with encryption
        response = self._send_to_server_encrypted(payload_bytes)
        print(f"ðŸ”’ Server response: {response}")

    def _load_file(self, file_path):
        """
        Load file from disk and return bytes.

        Args:
            file_path: Path to file

        Returns:
            bytes: File contents

        Raises:
            FileNotFoundError: If file does not exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(ERROR_FILE_NOT_FOUND)

        with open(file_path, FILE_MODE_READ_BINARY) as f:
            return f.read()

    def _encode_to_base64(self, file_bytes):
        """
        Encode file bytes to Base64 string.

        Args:
            file_bytes: Raw file bytes

        Returns:
            str: Base64 encoded string
        """
        return base64.b64encode(file_bytes).decode()

    def _detect_media_type(self, file_path):
        """
        Detect media type based on file extension.

        Args:
            file_path: Path to media file

        Returns:
            str: "video" if .mp4, "image" otherwise
        """
        ext = Path(file_path).suffix.lower()
        return MEDIA_TYPE_VIDEO if ext == VIDEO_EXTENSION else MEDIA_TYPE_IMAGE

    def _build_payload(self, username, media_type, b64_data):
        """
        Build JSON payload with media data.

        Args:
            username: Username for upload
            media_type: Type of media ("image" or "video")
            b64_data: Base64 encoded media data

        Returns:
            bytes: JSON payload as bytes
        """
        payload = {
            "username": username,
            "media_type": media_type,
            "data": b64_data
        }
        return json.dumps(payload).encode()

    def _send_to_server_encrypted(self, payload_bytes):
        """
        ðŸ”’ Send ENCRYPTED payload to server and receive response.

        Args:
            payload_bytes: Encoded payload to send

        Returns:
            str: Server response message
        """
        # Open TCP connection
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))

        try:
            # ðŸ”’ ENCRYPTION: Perform Diffie-Hellman key exchange
            print("Performing key exchange...")
            temp_conn = (s, None)
            encryption_key = key_exchange.KeyExchange.send_recv_key(temp_conn)
            encrypted_conn = (s, encryption_key)
            print(
                "Encryption established (key length: "
                f"{len(encryption_key)} bytes)"
            )
            # Encrypt the payload
            encrypted_payload = aes_cipher.AESCipher.encrypt(
                encryption_key,
                payload_bytes
            )

            # Send encrypted payload size
            self._send_payload_size(s, len(encrypted_payload))

            # Send encrypted payload
            s.sendall(encrypted_payload)
            print(f"Sent encrypted payload ({len(encrypted_payload)} bytes)")

            # Read server response
            response = s.recv(MSG_LEN).decode()
            return response

        finally:
            s.close()

    def _send_payload_size(self, sock, size):
        """
        Send payload size as 4-byte network-endian integer.

        Args:
            sock: Socket to send on
            size: Size in bytes
        """
        size_bytes = struct.pack(PAYLOAD_SIZE_FORMAT, size)
        sock.send(size_bytes)


def run(file_path, username=DEFAULT_USERNAME):
    """
    Helper function to send a file in one line with ENCRYPTION.

    Args:
        file_path: Path to media file to upload
        username: Username to associate with upload
    """
    client = MediaClient()
    client.send_media(file_path, username)
