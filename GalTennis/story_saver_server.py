import socket
import base64
import json
import struct
import os
import time
from pathlib import Path

STORIES_FOLDER = "stories"

class MediaServer:
    def __init__(self, host='127.0.0.1', port=3333):
        self.host = host
        self.port = port
        Path(STORIES_FOLDER).mkdir(exist_ok=True)

    def start(self):
        """Listens for 1 client per run."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(1)
        print(f"Server listening on {self.host}:{self.port}")

        client_socket, addr = server_socket.accept()
        print(f"Client connected: {addr}")

        try:
            self.handle_client(client_socket)
        finally:
            client_socket.close()
            server_socket.close()
            print("Server closed\n")

    def handle_client(self, client_socket):
        size_data = client_socket.recv(4)
        if not size_data:
            return

        payload_len = struct.unpack('!I', size_data)[0]
        data = b''
        while len(data) < payload_len:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            data += chunk

        payload = json.loads(data.decode())
        media_b64 = payload["data"]
        media_type = payload.get("media_type", "image")  # "image" / "video"
        username = payload.get("username", "user")

        file_bytes = base64.b64decode(media_b64)

        timestamp = int(time.time())
        ext = ".mp4" if media_type == "video" else ".jpg"

        # אפשר גם פשוט 'story.jpg' או 'story.mp4' אם רוצים לדרוס תמיד
        filename = f"story_{username}_{timestamp}{ext}"
        full_path = os.path.join(STORIES_FOLDER, filename)

        with open(full_path, "wb") as f:
            f.write(file_bytes)

        print(f"Saved story → {full_path}")
        client_socket.send(b"OK: story received")


def run():
    server = MediaServer()
    server.start()
