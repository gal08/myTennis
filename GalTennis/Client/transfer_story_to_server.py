"""
Gal Haham
Media file uploader client.
Converts images/videos to Base64 and sends
them to the media server via TCP.
"""
import socket
import base64
import json
import struct
import os
from pathlib import Path
from Read_server_ip import readServerIp

MSG_LEN = 1024
HOST = readServerIp()
PORT = 3333


class MediaClient:
    """
    MediaClient sends image/video files to a remote server.


    Responsibilities:
    - Load a media file (image or mp4).
    - Convert file to Base64 encoded string.
    - Build a JSON payload containing file + metadata.
    - Send payload length first (for framing), then the data.
    - Read a short server response.
    """
    def __init__(self, host=HOST, port=PORT):
        # Save connection details
        self.host = host
        self.port = port

    def send_media(self, file_path, username="user"):
        """
            Sends a media file (image or video) to the server.

            Steps performed:
            1. Verifies that the file exists.
            2. Reads the file as raw bytes.
            3. Converts the file into Base64 so it can be sent as text.
            4. Detects whether the file is an image
             or a video based on extension.
            5. Builds a JSON payload that contains:
                 - username
                 - media type (image/video)
                 - base64 media data
            6. Opens a TCP connection to the server.
            7. Sends the size of the payload (4 bytes)
            and then the payload itself.
            8. Waits for a short response from the server and prints it.
        """
        # Validate file path
        if not os.path.exists(file_path):
            raise FileNotFoundError("file not found")
        # Read file bytes
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        # Encode file to base64 text (safe for JSON)
        b64_data = base64.b64encode(file_bytes).decode()
        # Detect media type by file extension
        ext = Path(file_path).suffix.lower()
        media_type = "video" if ext == ".mp4" else "image"
        # Build payload
        payload = {
            "username": username,
            "media_type": media_type,
            "data": b64_data
        }
        # Convert to bytes
        payload_bytes = json.dumps(payload).encode()
        # Open TCP connection
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        # Send payload length as 4 bytes (network endian)
        s.send(struct.pack("!I", len(payload_bytes)))
        # Send payload itself
        s.sendall(payload_bytes)
        # Read short server ACK
        response = s.recv(MSG_LEN).decode()
        print("Server:", response)
        s.close()


def run(file_path, username="user"):
    """Helper function to send a file in one line."""
    client = MediaClient()
    client.send_media(file_path, username)
