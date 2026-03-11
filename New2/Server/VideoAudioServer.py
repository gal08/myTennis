"""
Gal Haham
Video & Audio Streaming Server
FIXED: Server runs indefinitely - no accept timeout
FIXED: Singleton pattern - one server instance always running
FIXED: update_video() swaps the video without restarting the server
FIXED: Client is receive-only, server initiates all key exchange
"""
import threading
import socket
import os
import key_exchange
from ClientHandler import ClientHandler

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 9999
MAX_PENDING_CONNECTIONS = 10
MAX_CONCURRENT_STREAMS = 10
SOCKET_REUSE_ADDRESS = 1

# ── Per-video server registry (video_path → (server, thread, port)) ────────────
_video_servers: dict = {}          # video_path → VideoAudioServer instance
_video_threads: dict = {}          # video_path → Thread
_video_ports: dict  = {}           # video_path → port
_registry_lock = threading.Lock()

VIDEO_PORT_START = 9900            # טווח פורטים לסרטונים
VIDEO_PORT_END   = 9999


class VideoAudioServer:
    """
    Encrypted video/audio streaming server.
    Runs forever once started; new clients get whatever video_path is current.
    """

    def __init__(self, video_path: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.video_path = video_path        # updated via update_video(), never restarts
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.active_clients = []
        self._client_lock = threading.Lock()
        self._client_counter = 0

    # ── Public API ─────────────────────────────────────────────────────────────

    def update_video(self, new_path: str):
        """Swap the video for the next connecting clients (no restart needed)."""
        self.video_path = new_path
        print(f"[VideoServer] Video updated → {new_path}")

    def start(self):
        """Block forever accepting clients. Call from a daemon thread."""
        try:
            self._create_server_socket()
            self.is_running = True
            print(f"[VideoServer] Listening on {self.host}:{self.port} (runs forever)")
            self._accept_loop()
        except Exception as e:
            print(f"[VideoServer] Fatal: {e}")
        finally:
            self._teardown()

    def stop(self):
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        print("[VideoServer] Stopped")

    # ── Private helpers ────────────────────────────────────────────────────────

    def _create_server_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, SOCKET_REUSE_ADDRESS)
        s.bind((self.host, self.port))
        s.listen(MAX_PENDING_CONNECTIONS)
        self.server_socket = s

    def _accept_loop(self):
        """Accept clients indefinitely - NO timeout so the thread never exits."""
        while self.is_running:
            try:
                # Blocking accept - stays here until a client connects
                client_socket, address = self.server_socket.accept()
            except OSError:
                # Socket was closed (server.stop() called)
                break
            except Exception as e:
                if self.is_running:
                    print(f"[VideoServer] Accept error: {e}")
                continue

            with self._client_lock:
                if len(self.active_clients) >= MAX_CONCURRENT_STREAMS:
                    print(f"[VideoServer] Max clients reached, rejecting {address}")
                    client_socket.close()
                    continue
                self._client_counter += 1
                client_id = self._client_counter

            t = threading.Thread(
                target=self._handle_client,
                args=(client_socket, address, client_id),
                daemon=True,
                name=f"VideoClient-{client_id}"
            )
            t.start()

    def _handle_client(self, client_socket: socket.socket, address: tuple, client_id: int):
        """
        Server-side client session.
        Server initiates key exchange → client is purely receive-only.
        """
        with self._client_lock:
            self.active_clients.append(address)

        print(f"[VideoServer] Client #{client_id} connected from {address}")

        try:
            # Server initiates DH key exchange (recv_send_key = server role)
            conn = (client_socket, None)
            encryption_key = key_exchange.KeyExchange.recv_send_key(conn)
            encrypted_conn = (client_socket, encryption_key)

            print(f"[VideoServer] Client #{client_id} encrypted, streaming: {self.video_path}")

            handler = ClientHandler(
                self.video_path,
                encrypted_conn,
                address,
                client_id
            )
            handler.handle_streaming()

        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError):
            pass  # Normal disconnect - silent
        except Exception as e:
            print(f"[VideoServer] Client #{client_id} error: {e}")
        finally:
            with self._client_lock:
                if address in self.active_clients:
                    self.active_clients.remove(address)
                remaining = len(self.active_clients)

            print(f"[VideoServer] Client #{client_id} disconnected. Active: {remaining}/{MAX_CONCURRENT_STREAMS}")
            try:
                client_socket.close()
            except Exception:
                pass

    def _teardown(self):
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass


# ── Module-level functions used by Methods.py and Server.py ───────────────────

def _find_free_port() -> int:
    """מחפש פורט פנוי בטווח הסרטונים. חייב להיקרא בתוך _registry_lock."""
    used = set(_video_ports.values())
    for p in range(VIDEO_PORT_START, VIDEO_PORT_END + 1):
        if p not in used:
            return p
    return None


def ensure_video_server_running(video_path: str = "") -> dict:
    """
    כל video_path שונה → שרת נפרד על פורט נפרד.
    - אם השרת לסרטון כבר רץ → מחזיר את הפורט הקיים.
    - אחרת → מקצה פורט חדש ומפעיל שרת חדש.
    מחזיר dict עם {"server": ..., "port": ...}
    """
    with _registry_lock:
        # שרת קיים לאותו קובץ?
        if video_path and video_path in _video_servers:
            srv = _video_servers[video_path]
            thr = _video_threads[video_path]
            if srv.is_running and thr.is_alive():
                port = _video_ports[video_path]
                print(f"[VideoServer] Reusing existing server for '{video_path}' on port {port}")
                return {"server": srv, "port": port}
            else:
                # שרת מת – ננקה ונפעיל מחדש
                del _video_servers[video_path]
                del _video_threads[video_path]
                del _video_ports[video_path]

        # פורט ריק ← video_path ריק (קריאת אתחול בלבד, אין מה להפעיל)
        if not video_path:
            return {"server": None, "port": None}

        # מצא פורט פנוי
        port = _find_free_port()
        if port is None:
            raise RuntimeError("No available ports for video streaming (9900-9999 full)")

        print(f"[VideoServer] Starting new server for '{video_path}' on port {port}...")
        srv = VideoAudioServer(video_path, DEFAULT_HOST, port)
        thr = threading.Thread(
            target=srv.start,
            daemon=True,
            name=f"VideoServer-{port}-{os.path.basename(video_path)}"
        )

        _video_servers[video_path] = srv
        _video_threads[video_path] = thr
        _video_ports[video_path]   = port

        thr.start()
        print(f"[VideoServer] Server started on port {port} for '{video_path}'")
        return {"server": srv, "port": port}


def run_video_player_server(video_path: str):
    """
    Legacy entry point kept for compatibility.
    Now just delegates to ensure_video_server_running().
    """
    ensure_video_server_running(video_path)