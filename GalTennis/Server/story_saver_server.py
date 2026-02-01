"""
Gal Haham
Media upload server for stories - ENCRYPTED VERSION
Receives ENCRYPTED Base64-encoded photos/videos from clients
and saves them to the stories folder
ENHANCED: Added full encryption support via Diffie-Hellman + AES
"""
import socket
import base64
import json
import struct
import os
import time
from pathlib import Path
import key_exchange
import aes_cipher
from Protocol import Protocol

STORIES_FOLDER = "stories"
HOST = '0.0.0.0'
PORT = 3333
SOCKET_OPTION_ENABLED = 1
RECV_CHUNK_SIZE_BYTES = 4096
MULTI_CONNECTION_BACKLOG = 5
SINGLE_ELEMENT_INDEX = 0
SIZE_HEADER_BYTES = 4
SOCK_INDEX = 0
KEY_INDEX = 1


class MediaServer:
    """
    TCP media server that receives ENCRYPTED photos or videos from clients,
    decrypts them, decodes them, and saves them into the stories folder.
    ENHANCED: Full encryption support
    """
    def __init__(self, host=HOST, port=PORT):
        """Initializes the MediaServer."""
        self.host = host
        self.port = port
        self.is_running = False
        Path(STORIES_FOLDER).mkdir(exist_ok=True)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            SOCKET_OPTION_ENABLED
        )
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MULTI_CONNECTION_BACKLOG)
        self.conn = (0,0)

    def start(self):
        """
        Start the server and listen for multiple encrypted clients.
        Runs continuously until stopped.
        """


        try:

            self.is_running = True
            print(
                f"[ENCRYPTED STORY UPLOAD] Server listening on "
                f"{self.host}: {self.port}"
            )

            while self.is_running:
                try:
                    # Accept new client connection
                    client_socket, addr = self.server_socket.accept()
                    print(f"[STORY UPLOAD] Client connected: {addr}")

                    # Establish encryption
                    self.conn = self._establish_encryption(
                        client_socket,
                        addr
                    )

                    # Handle this encrypted client
                    self.handle_client()

                    # Close client connection
                    client_socket.close()
                    print(f"[STORY UPLOAD] Client {addr} disconnected")

                except Exception as e:
                    print(f"[STORY UPLOAD] Error handling client: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

        except OSError as e:
            print(f"[STORY UPLOAD] Socket error: {e}")
        finally:
            self.server_socket.close()
            print("[STORY UPLOAD] Server stopped")

    def _establish_encryption(self, client_socket, addr):
        """
        Establish encryption with client via Diffie-Hellman.

        Args:
            client_socket: Client socket
            addr: Client address

        Returns:
            tuple: (socket, encryption_key) or None if failed
        """
        try:
            print(f"[STORY UPLOAD] Performing key exchange with {addr}...")
            temp_conn = (client_socket, None)
            encryption_key = key_exchange.KeyExchange.recv_send_key(temp_conn)
            encrypted_conn = (client_socket, encryption_key)
            print(f"[STORY UPLOAD] Encryption established with {addr} "
                  f"(key length: {len(encryption_key)} bytes)")
            return encrypted_conn
        except Exception as e:
            print(f"[STORY UPLOAD] Key exchange failed with {addr}: {e}")
            return None

    def handle_client(self):
        """
        Receives an ENCRYPTED media upload request
         from the client and saves it.

        Args:
            encrypted_conn: Tuple of (socket, encryption_key)
        """
        client_socket = self.conn[SOCK_INDEX]

        try:
            # Step 1: Receive encrypted data from client
            #payload_data = self._receive_encrypted_payload(encrypted_conn)
            payload_data = Protocol.recv(self.conn)
            if not payload_data:
                return

            # Step 2: Parse and extract media info
            media_info = self._parse_media_payload(payload_data)
            if not media_info:
                return

            # Step 3: Save media file
            saved_path = self._save_media_file(media_info)

            # Step 4: Send success response
            request_data = json.dumps({
                "type": 'good',
                "payload": "OK: encrypted story received"
            })
            Protocol.send(request_data, self.conn)

        except json.JSONDecodeError as e:
            print(f"[STORY UPLOAD] JSON error: {e}")
            self._send_error_response("Invalid JSON")
        except Exception as e:
            print(f"[STORY UPLOAD] Error: {e}")
            import traceback
            traceback.print_exc()
            self._send_error_response(str(e))

    def _parse_media_payload(self, payload_data):
        """
        Parse JSON payload and extract media information.

        Args:
            payload_data: Decrypted payload bytes

        Returns:
            dict: Media info or None if failed
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

        Args:
            media_info: Media information dict

        Returns:
            str: Full path where file was saved
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
        """Generate a unique filename based on
        username, timestamp, and type."""
        timestamp = int(time.time())
        ext = ".mp4" if media_type == "video" else ".jpg"
        return f"story_{username}_{timestamp}{ext}"

    def _send_error_response(self, error_message):
        """Send error response to client."""
        request_data = json.dumps({
            "type": 'error',
            "payload": f"ERROR: {error_message}"
        })
        Protocol.send(request_data, self.conn)

    def stop(self):
        """Stop the server"""
        self.is_running = False


def run():
    """
    Convenience function to create and start an ENCRYPTED MediaServer instance.
    """
    server = MediaServer()
    server.start()


if __name__ == "__main__":
    run()
