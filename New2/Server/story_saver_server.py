"""
Gal Haham
Media upload server for stories - ENCRYPTED VERSION
FIXED: conn=(0,0) bug removed - conn set only after real socket accept
FIXED: True multi-client - each client in its own thread
FIXED: Client socket passed properly to each handler thread
"""
import socket
import base64
import json
import os
import time
import threading
from pathlib import Path
import key_exchange
from Protocol import Protocol

STORIES_FOLDER = "stories"
HOST = '0.0.0.0'
PORT = 3333
SOCKET_OPTION_ENABLED = 1
MAX_PENDING_CONNECTIONS = 5
SOCK_INDEX = 0
KEY_INDEX = 1


class MediaServer:
    """
    TCP media server - receives encrypted photos/videos and saves them.
    Multi-client: each connection handled in its own thread.
    """

    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.is_running = False
        Path(STORIES_FOLDER).mkdir(exist_ok=True)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, SOCKET_OPTION_ENABLED
        )
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MAX_PENDING_CONNECTIONS)

        self._client_counter = 0
        self._counter_lock = threading.Lock()

    def start(self):
        self.is_running = True
        print(f"[StoryUpload] Listening on {self.host}:{self.port}")

        while self.is_running:
            try:
                # Blocking accept - no timeout
                client_socket, addr = self.server_socket.accept()

                with self._counter_lock:
                    self._client_counter += 1
                    client_id = self._client_counter

                print(f"[StoryUpload] Client #{client_id} connected from {addr}")

                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr, client_id),
                    daemon=True,
                    name=f"StoryUpload-{client_id}"
                ).start()

            except OSError:
                if self.is_running:
                    print("[StoryUpload] Socket error")
                break
            except Exception as e:
                print(f"[StoryUpload] Accept error: {e}")

        self.server_socket.close()
        print("[StoryUpload] Server stopped")

    def _handle_client(self, client_socket: socket.socket, addr: tuple, client_id: int):
        """Each client: key exchange → receive file → save → respond."""
        conn = None
        try:
            # Key exchange
            temp_conn = (client_socket, None)
            key = key_exchange.KeyExchange.recv_send_key(temp_conn)
            conn = (client_socket, key)
            print(f"[StoryUpload #{client_id}] Encryption ready")

            # Receive payload
            payload_str = Protocol.recv(conn)
            if not payload_str:
                return

            # Parse JSON
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError as e:
                print(f"[StoryUpload #{client_id}] JSON error: {e}")
                self._send_error(conn, "Invalid JSON")
                return

            # Save file
            saved_path = self._save_media(payload, client_id)
            if saved_path:
                print(f"[StoryUpload #{client_id}] Saved: {saved_path}")
                Protocol.send(json.dumps({"type": "good", "payload": "OK"}), conn)
            else:
                self._send_error(conn, "Failed to save file")

        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError):
            pass  # Normal disconnect
        except Exception as e:
            print(f"[StoryUpload #{client_id}] Error: {e}")
            if conn:
                self._send_error(conn, str(e))
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
            print(f"[StoryUpload #{client_id}] Disconnected")

    def _save_media(self, payload: dict, client_id: int) -> str:
        try:
            media_b64 = payload.get("data", "")
            media_type = payload.get("media_type", "image")
            username = payload.get("username", "user")

            file_bytes = base64.b64decode(media_b64)

            timestamp = int(time.time())
            ext = ".mp4" if media_type == "video" else ".jpg"
            filename = f"story_{username}_{timestamp}{ext}"
            full_path = os.path.join(STORIES_FOLDER, filename)

            with open(full_path, "wb") as f:
                f.write(file_bytes)

            return full_path
        except Exception as e:
            print(f"[StoryUpload #{client_id}] Save error: {e}")
            return None

    def _send_error(self, conn, message: str):
        try:
            Protocol.send(json.dumps({"type": "error", "payload": f"ERROR: {message}"}), conn)
        except Exception:
            pass

    def stop(self):
        self.is_running = False
        try:
            self.server_socket.close()
        except Exception:
            pass


def run():
    server = MediaServer()
    server.start()


if __name__ == "__main__":
    run()
