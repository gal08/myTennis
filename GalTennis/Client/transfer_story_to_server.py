"""
Gal Haham
Media file uploader client.
Converts images/videos to Base64 and sends them to the media server via TCP.
REFACTORED: Split long method, added comprehensive documentation,
added missing constants.
"""
import socket
import base64
import json
import struct
import os
from pathlib import Path


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


class MediaClient:
    """
    MediaClient sends image/video files to a remote server.

    Responsibilities:
    - Load a media file (image or mp4).
    - Convert file to Base64 encoded string.
    - Build a JSON payload containing file + metadata.
    - Send payload length first (for framing), then the data.
    - Read a short server response.

    REFACTORED: Long method split into focused helper methods.
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
        Send a media file (image or video) to the server.

        Steps performed:
        1. Verifies that the file exists.
        2. Reads the file as raw bytes.
        3. Converts the file into Base64 so it can be sent as text.
        4. Detects whether the file is an image or a video based on extension.
        5. Builds a JSON payload that contains:
             - username
             - media type (image/video)
             - base64 media data
        6. Opens a TCP connection to the server.
        7. Sends the size of the payload (4 bytes) and then the payload itself.
        8. Waits for a short response from the server and prints it.

        Args:
            file_path: Path to media file (image or video)
            username: Username to associate with the upload

        Raises:
            FileNotFoundError: If file does not exist

        REFACTORED: Split into helper methods for better organization.
        """
        # Load and encode file
        file_bytes = self._load_file(file_path)
        b64_data = self._encode_to_base64(file_bytes)

        # Detect media type and build payload
        media_type = self._detect_media_type(file_path)
        payload_bytes = self._build_payload(username, media_type, b64_data)

        # Send to server
        response = self._send_to_server(payload_bytes)
        print("Server:", response)

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

    def _send_to_server(self, payload_bytes):
        """
        Send payload to server and receive response.

        Args:
            payload_bytes: Encoded payload to send

        Returns:
            str: Server response message
        """
        # Open TCP connection
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))

        try:
            # Send payload size first (for framing)
            self._send_payload_size(s, len(payload_bytes))

            # Send payload itself
            s.sendall(payload_bytes)

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
    Helper function to send a file in one line.

    Args:
        file_path: Path to media file to upload
        username: Username to associate with upload
    """
    client = MediaClient()
    client.send_media(file_path, username)
