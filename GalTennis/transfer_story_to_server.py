import socket
import base64
import json
import struct
import os
from pathlib import Path

class MediaClient:
    def __init__(self, host='127.0.0.1', port=3333):
        self.host = host
        self.port = port

    def send_media(self, file_path, username="user"):
        if not os.path.exists(file_path):
            raise FileNotFoundError("file not found")

        # קרא את הקובץ והצפן ל-base64
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        b64_data = base64.b64encode(file_bytes).decode()

        ext = Path(file_path).suffix.lower()
        media_type = "video" if ext == ".mp4" else "image"

        payload = {
            "username": username,
            "media_type": media_type,
            "data": b64_data
        }

        payload_bytes = json.dumps(payload).encode()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.send(struct.pack("!I", len(payload_bytes)))
        s.sendall(payload_bytes)

        response = s.recv(1024).decode()
        print("Server:", response)
        s.close()


def run(file_path, username="user"):
    client = MediaClient()
    client.send_media(file_path, username)
