"""
Gal Haham
Media upload server for stories.
Receives Base64-encoded photos/videos from clients
and saves them to the stories folder.
REFACTORED: handle_client split into smaller helper methods
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
            print(
                f"[STORY UPLOAD] Server listening on "
                f"{self.host}: {self.port}"
            )
            print(f"[STORY UPLOAD] Ready to receive story uploads...")

            while self.is_running:
                try:
                    # Accept new client connection
                    client_socket, addr = server_socket.accept()
                    print(f"[STORY UPLOAD] Client connected: {addr}")

                    # Handle this client
                    self.handle_client(client_socket)

                    # Close client connection
                    client_socket.close()
                    print(f"[STORY UPLOAD] Client {addr} disconnected")

                except Exception as e:
                    print(f"[STORY UPLOAD] Error handling client: {e}")
                    continue

        except OSError as e:
            print(f"[STORY UPLOAD] Socket error: {e}")
        finally:
            server_socket.close()
            print("[STORY UPLOAD] Server stopped")

    def handle_client(self, client_socket):
        """
        Receives a media upload request from the client and saves it.
        REFACTORED: Delegates to helper methods for clarity.
        """
        try:
            # Step 1: Receive data from client
            payload_data = self._receive_payload(client_socket)
            if not payload_data:
                return

            # Step 2: Parse and extract media info
            media_info = self._parse_media_payload(payload_data)
            if not media_info:
                return

            # Step 3: Save media file
            saved_path = self._save_media_file(media_info)

            # Step 4: Send success response
            self._send_success_response(
                client_socket,
                saved_path,
                len(media_info['file_bytes'])
            )

        except json.JSONDecodeError as e:
            print(f"[STORY UPLOAD] JSON error: {e}")
            self._send_error_response(client_socket, "Invalid JSON")
        except Exception as e:
            print(f"[STORY UPLOAD] Error: {e}")
            self._send_error_response(client_socket, str(e))

    def _receive_payload(self, client_socket):
        """
        Receive the complete payload from client.
        Returns payload data or None if failed.
        """
        # Receive size header
        size_data = client_socket.recv(SIZE_HEADER_BYTES)
        if not size_data:
            print("[STORY UPLOAD] No data received")
            return None

        # Get payload length
        payload_len = struct.unpack('!I', size_data)[SINGLE_ELEMENT_INDEX]
        print(f"[STORY UPLOAD] Expecting {payload_len} bytes")

        # Receive full payload in chunks
        data = self._receive_data_chunks(client_socket, payload_len)

        # Verify received data length
        if len(data) != payload_len:
            print(
                f"[STORY UPLOAD] Warning: Expected {payload_len} bytes, "
                f"got {len(data)}"
            )
        return data

    def _receive_data_chunks(self, client_socket, total_bytes):
        """Receive data in chunks until complete."""
        data = b''
        while len(data) < total_bytes:
            remaining = total_bytes - len(data)
            chunk_size = min(RECV_CHUNK_SIZE_BYTES, remaining)
            chunk = client_socket.recv(chunk_size)
            if not chunk:
                break
            data += chunk
        return data

    def _parse_media_payload(self, payload_data):
        """
        Parse JSON payload and extract media information.
        Returns dict with media info or None if failed.
        """
        # Parse JSON payload
        payload = json.loads(payload_data.decode())

        # Extract fields
        media_b64 = payload["data"]
        media_type = payload.get("media_type", "image")
        username = payload.get("username", "user")

        # Decode base64 to binary
        file_bytes = base64.b64decode(media_b64)

        return {
            'file_bytes': file_bytes,
            'media_type': media_type,
            'username': username
        }

    def _save_media_file(self, media_info):
        """
        Save media file to disk with unique filename.
        Returns the full path where file was saved.
        """
        # Generate unique filename
        filename = self._generate_unique_filename(
            media_info['username'],
            media_info['media_type']
        )

        full_path = os.path.join(STORIES_FOLDER, filename)

        # Save file
        with open(full_path, "wb") as f:
            f.write(media_info['file_bytes'])

        return full_path

    def _generate_unique_filename(self, username, media_type):
        """Generate a unique filename based
        on username, timestamp, and type."""
        timestamp = int(time.time())
        ext = ".mp4" if media_type == "video" else ".jpg"
        return f"story_{username}_{timestamp}{ext}"

    def _send_success_response(self, client_socket, saved_path, file_size):
        """Send success response to client and log the save."""
        print(
            f"[STORY UPLOAD] Saved story"
            f"{saved_path} ({file_size} bytes)"
        )
        try:
            client_socket.send(b"OK: story received")
        except:
            pass

    def _send_error_response(self, client_socket, error_message):
        """Send error response to client."""
        try:
            client_socket.send(f"ERROR: {error_message}".encode())
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
