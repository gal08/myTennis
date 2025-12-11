"""
Gal Haham
Media upload server for stories.
Receives Base64-encoded photos/videos from clients
and saves them to the stories folder.
IMPROVED: Can handle multiple uploads without restarting
"""
import socket
import base64
import json
import struct
import os
import time
from pathlib import Path

STORIES_FOLDER = "stories"
HOST = '0.0.0.0'
PORT = 3333
SOCKET_OPTION_ENABLED = 1
RECV_CHUNK_SIZE_BYTES = 4096
MULTI_CONNECTION_BACKLOG = 5
SINGLE_ELEMENT_INDEX = 0
SIZE_HEADER_BYTES = 4


class MediaServer:
    """
    TCP media server that receives photos or videos from clients,
    decodes them, and saves them into the stories folder.

    IMPROVED: Runs continuously and accepts multiple uploads.
    """
    def __init__(self, host=HOST, port=PORT):
        """Initializes the MediaServer."""
        self.host = host
        self.port = port
        self.is_running = False
        Path(STORIES_FOLDER).mkdir(exist_ok=True)

    def start(self):
        """
        Start the server and listen for multiple clients.
        Runs continuously until stopped.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            SOCKET_OPTION_ENABLED
        )

        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(MULTI_CONNECTION_BACKLOG)
            self.is_running = True

            while self.is_running:
                try:
                    # Accept new client connection
                    client_socket, addr = server_socket.accept()

                    # Handle this client
                    self.handle_client(client_socket)

                    # Close client connection
                    client_socket.close()

                except Exception as e:
                    # Silently continue on error
                    continue

        except OSError as e:
            print(f"[ERROR] Story upload server socket error: {e}")
        finally:
            server_socket.close()

    def handle_client(self, client_socket):
        """
        Receives a media upload request from the client and saves it.
        """
        try:
            # Receive size header
            size_data = client_socket.recv(SIZE_HEADER_BYTES)
            if not size_data:
                return

            # Get payload length
            payload_len = struct.unpack('!I', size_data)[SINGLE_ELEMENT_INDEX]

            # Receive full payload
            data = b''
            while len(data) < payload_len:
                remaining = payload_len - len(data)
                chunk_size = min(RECV_CHUNK_SIZE_BYTES, remaining)
                chunk = client_socket.recv(chunk_size)
                if not chunk:
                    break
                data += chunk

            if len(data) != payload_len:
                return

            # Parse JSON payload
            payload = json.loads(data.decode())
            media_b64 = payload["data"]
            media_type = payload.get("media_type", "image")
            username = payload.get("username", "user")

            # Decode base64 to binary
            file_bytes = base64.b64decode(media_b64)

            # Generate unique filename
            timestamp = int(time.time())
            ext = ".mp4" if media_type == "video" else ".jpg"
            filename = f"story_{username}_{timestamp}{ext}"
            full_path = os.path.join(STORIES_FOLDER, filename)

            # Save file
            with open(full_path, "wb") as f:
                f.write(file_bytes)

            # Send success response
            client_socket.send(b"OK: story received")

        except json.JSONDecodeError:
            try:
                client_socket.send(b"ERROR: Invalid JSON")
            except:
                pass
        except Exception:
            try:
                client_socket.send(b"ERROR: Upload failed")
            except:
                pass

    def stop(self):
        """Stop the server"""
        self.is_running = False


def run():
    """
    Convenience function to create and start a MediaServer instance.
    Used when this file is executed as a script or imported.
    """
    server = MediaServer()
    server.start()


if __name__ == "__main__":
    run()