"""
Gal Haham
Main Tennis Social server application.
Routes client requests, manages handlers, and coordinates video/story streaming servers.
FIXED: Video streaming server starts automatically when RequestMethodsHandler is created.
       No extra code needed in Server.__init__ for video.
"""
import socket
import json
import threading
import time
import os
import key_exchange
from Protocol import Protocol
from Methods import RequestMethodsHandler
from handle_show_all_stories import run as run_stories_display_server

try:
    from handle_show_all_videos import run as run_videos_display_server
except ImportError:
    run_videos_display_server = None

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000
MAX_PENDING_CONNECTIONS = 5
SOCKET_REUSE_ADDRESS = 1

VIDEO_FOLDER = "videos"
STORY_FOLDER = "stories"
HALF_SECOND = 0.5
SEPARATOR_LENGTH = 50
SEPARATOR_CHAR = "="
JSON_START_CHAR = '{'
NOT_FOUND_INDEX = -1

KEY_TYPE = 'type'
KEY_PAYLOAD = 'payload'
KEY_STATUS = 'status'
KEY_MESSAGE = 'message'


class Server:
    """Main Tennis Social server."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.running = False
        self.video_thumbnail_server_running = False
        self.story_thumbnail_server_running = False

        os.makedirs(VIDEO_FOLDER, exist_ok=True)
        os.makedirs(STORY_FOLDER, exist_ok=True)

        # ── This single line also starts the persistent video server on port 9999
        #    because RequestMethodsHandler.__init__ calls ensure_video_server_running().
        #    Nothing else is needed here for video streaming.
        self.methods_handler = RequestMethodsHandler()

        self._create_server_socket()

    def start(self):
        self._print_startup_banner()

        # Thumbnail servers (unchanged)
        self.start_video_thumbnail_server()
        self.start_story_thumbnail_server()

        try:
            self._run_server_loop()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"Server error: {e}")
            self.stop()

    def _create_server_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, SOCKET_REUSE_ADDRESS
        )
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MAX_PENDING_CONNECTIONS)
        self.running = True

    def _print_startup_banner(self):
        sep = SEPARATOR_CHAR * SEPARATOR_LENGTH
        print(sep)
        print("Tennis Social Server")
        print(sep)
        print(f"Main Server  : {self.host}:{self.port}")
        print(f"Video Stream : port 9999  (always on)")
        print(sep)
        print("Waiting for clients...")
        print(sep)

    def _run_server_loop(self):
        print("[Server] Main loop started")
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"\n{'=' * 60}")
                print(f"NEW CLIENT: {addr}")
                print(f"{'=' * 60}")

                threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr),
                    daemon=True
                ).start()

            except OSError:
                if not self.running:
                    break
            except Exception as e:
                print(f"[Server] Accept error: {e}")

    def stop(self):
        self.running = False
        try:
            self.server_socket.close()
        except Exception:
            pass
        print("\nServer stopped.")

    # ── Thumbnail servers (unchanged) ─────────────────────────────────────────

    def start_video_thumbnail_server(self):
        if self.video_thumbnail_server_running:
            return

        def _run():
            try:
                print("Starting Video Thumbnail Server (port 2223)...")
                if run_videos_display_server:
                    run_videos_display_server()
                else:
                    print("[WARN] Video thumbnail server not available")
            except Exception as e:
                print(f"[ERROR] Video thumbnail server: {e}")

        threading.Thread(target=_run, daemon=True).start()
        self.video_thumbnail_server_running = True
        time.sleep(HALF_SECOND)

    def start_story_thumbnail_server(self):
        if self.story_thumbnail_server_running:
            return

        def _run():
            try:
                print("Starting Story Thumbnail Server (port 2222)...")
                run_stories_display_server()
            except Exception as e:
                print(f"[ERROR] Story thumbnail server: {e}")

        threading.Thread(target=_run, daemon=True).start()
        self.story_thumbnail_server_running = True
        time.sleep(HALF_SECOND)

    # ── Client handler ────────────────────────────────────────────────────────

    def handle_client(self, client_socket: socket.socket, addr: tuple):
        conn = (client_socket, None)
        try:
            # Key exchange (server role)
            print(f"[{addr}] Key exchange...")
            key = key_exchange.KeyExchange.recv_send_key(conn)
            conn = (client_socket, key)
            print(f"[{addr}] Encrypted session ready")

            while True:
                request_data = self._receive_request(conn, addr)
                if not request_data:
                    print(f"[{addr}] Client disconnected")
                    break

                print(f"[{addr}] Request: {request_data.get('type')}")
                response = self.methods_handler.route_request(request_data)

                if not self._send_response(conn, response, addr):
                    print(f"[{addr}] Send failed - client disconnected")
                    break

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            print(f"[{addr}] Client disconnected abruptly")
        except OSError as e:
            if e.errno in (10053, 10054, 104, 32):
                print(f"[{addr}] Connection lost")
            else:
                print(f"[{addr}] Socket error: {e}")
        except Exception as e:
            print(f"[{addr}] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._close_client_socket(client_socket, addr)

    def _receive_request(self, conn, addr) -> dict:
        try:
            data_raw = Protocol.recv(conn)
            if not data_raw:
                return None

            start = data_raw.find(JSON_START_CHAR)
            if start == NOT_FOUND_INDEX:
                return None

            return json.loads(data_raw[start:].strip())

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
            return None
        except json.JSONDecodeError:
            print(f"[{addr}] JSON decode error")
            return None
        except Exception as e:
            print(f"[{addr}] Receive error: {e}")
            return None

    def _send_response(self, conn, response: dict, addr) -> bool:
        try:
            Protocol.send(json.dumps(response), conn)
            return True
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
            return False
        except Exception as e:
            print(f"[{addr}] Send error: {e}")
            return False

    def _close_client_socket(self, client_socket: socket.socket, addr):
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            client_socket.close()
        except Exception:
            pass
        print(f"[{addr}] Connection closed")


if __name__ == '__main__':
    server_app = Server()
    server_app.start()