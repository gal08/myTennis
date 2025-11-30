"""
Gal Haham
Media upload server for stories.
Receives Base64-encoded photos/videos from clients
and saves them to the stories folder.
"""
import socket
import base64
import json
import struct
import os
import time
from pathlib import Path

STORIES_FOLDER = "stories"
HOST = '127.0.0.1'
PORT = 3333
SOCKET_OPTION_ENABLED = 1
RECV_CHUNK_SIZE_BYTES = 4096
SINGLE_CONNECTION_BACKLOG = 1
SINGLE_ELEMENT_INDEX = 0
SIZE_HEADER_BYTES = 4


class MediaServer:
    """A simple TCP media server that receives either photos or videos
    sent by a client, decodes them, and saves
     them into the local stories folder."""
    def __init__(self, host=HOST, port=PORT):
        """Initializes the MediaServer."""
        self.host = host
        self.port = port
        Path(STORIES_FOLDER).mkdir(exist_ok=True)

    def start(self):
        """Listens for 1 client per run."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            SOCKET_OPTION_ENABLED
        )
        server_socket.bind((self.host, self.port))
        server_socket.listen(SINGLE_CONNECTION_BACKLOG)
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
        """
            Receives a media upload request from the client and saves it"""
        size_data = client_socket.recv(SIZE_HEADER_BYTES)
        if not size_data:
            return

        payload_len = struct.unpack('!I', size_data)[SINGLE_ELEMENT_INDEX]
        data = b''
        while len(data) < payload_len:
            chunk = client_socket.recv(RECV_CHUNK_SIZE_BYTES)
            if not chunk:
                break
            data += chunk

        payload = json.loads(data.decode())
        media_b64 = payload["data"]
        media_type = payload.get("media_type", "image")
        username = payload.get("username", "user")

        file_bytes = base64.b64decode(media_b64)

        timestamp = int(time.time())
        ext = ".mp4" if media_type == "video" else ".jpg"

        filename = f"story_{username}_{timestamp}{ext}"
        full_path = os.path.join(STORIES_FOLDER, filename)

        with open(full_path, "wb") as f:
            f.write(file_bytes)

        print(f"Saved story → {full_path}")
        client_socket.send(b"OK: story received")


def run():
    """
    Convenience function to create and start a MediaServer instance.
    Used when this file is executed as a script.
    """
    server = MediaServer()
    server.start()
