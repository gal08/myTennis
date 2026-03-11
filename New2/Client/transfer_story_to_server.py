"""
Gal Haham
Media file uploader client - ENCRYPTED VERSION
FIXED: {payload_bytes} set bug → now sends base64 string in JSON correctly
FIXED: Payload built and sent properly via Protocol.send
"""
import socket
import base64
import json
import os
from pathlib import Path
import key_exchange
from Protocol import Protocol

HOST = "127.0.0.1"
PORT = 3333

VIDEO_EXTENSION = ".mp4"
MEDIA_TYPE_VIDEO = "video"
MEDIA_TYPE_IMAGE = "image"
FILE_MODE_READ_BINARY = "rb"
DEFAULT_USERNAME = "user"
ERROR_FILE_NOT_FOUND = "File not found"

SOCK_INDEX = 0
KEY_INDEX = 1


class MediaClient:
    """
    Sends image/video files to the story upload server with encryption.
    Pipeline: load file → base64 → JSON → Protocol.send (encrypted)
    """

    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

        # Key exchange - client role
        temp_conn = (self.socket, None)
        key = key_exchange.KeyExchange.send_recv_key(temp_conn)
        self.conn = (self.socket, key)
        print(f"[MediaClient] Encryption ready ({len(key)} bytes)")

    def send_media(self, file_path: str, username: str = DEFAULT_USERNAME):
        """Load a media file, encode it, and send to server."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{ERROR_FILE_NOT_FOUND}: {file_path}")

        # Read and encode
        with open(file_path, FILE_MODE_READ_BINARY) as f:
            file_bytes = f.read()

        b64_data = base64.b64encode(file_bytes).decode()
        media_type = MEDIA_TYPE_VIDEO if Path(file_path).suffix.lower() == VIDEO_EXTENSION else MEDIA_TYPE_IMAGE

        # Build JSON payload
        payload = json.dumps({
            "username": username,
            "media_type": media_type,
            "data": b64_data          # ← FIXED: was {payload_bytes} (set bug)
        })

        # Send via encrypted Protocol
        Protocol.send(payload, self.conn)
        print(f"[MediaClient] Sent {media_type}: {file_path}")

        # Receive response
        response = Protocol.recv(self.conn)
        print(f"[MediaClient] Server response: {response}")
        return response

    def close(self):
        try:
            self.socket.close()
        except Exception:
            pass


def run(file_path: str, username: str = DEFAULT_USERNAME):
    """Send a file in one call."""
    client = MediaClient()
    try:
        client.send_media(file_path, username)
    finally:
        client.close()