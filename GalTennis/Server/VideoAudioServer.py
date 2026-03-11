"""
Gal Haham
Video & Audio Streaming Server
REFACTORED: Single port (9999) for all videos, multithreaded clients.
            Each PLAY_VIDEO request gets a short-lived ticket; the client
            sends the ticket on connect so the server knows which video to stream.
            No more per-video ports — everything runs on DEFAULT_PORT (9999).
"""
import threading
import socket
import os
import uuid
import time
import key_exchange
from ClientHandler import ClientHandler

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 9999
MAX_PENDING_CONNECTIONS = 20
MAX_CONCURRENT_STREAMS = 20
SOCKET_REUSE_ADDRESS = 1
TICKET_TTL_SECONDS = 30        # ticket expires if client never connects

# ── Global singleton ──────────────────────────────────────────────────────────
_server_instance: "VideoAudioServer | None" = None
_server_thread:   "threading.Thread | None" = None
_server_lock = threading.Lock()


class VideoAudioServer:
    """
    Single encrypted video/audio streaming server on one fixed port.
    Clients identify which video they want via a one-time ticket sent
    immediately after the TCP connection is established (before key exchange).
    """

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.active_clients = []
        self._client_lock = threading.Lock()
        self._client_counter = 0

        # ticket_id → {"video_path": str, "expires": float}
        self._tickets: dict = {}
        self._ticket_lock = threading.Lock()

    # ── Ticket API (called by Methods.py / ensure_video_server_running) ────────

    def create_ticket(self, video_path: str) -> str:
        """
        Reserve a slot for one client to stream video_path.
        Returns a short ticket string the client must send on connect.
        Tickets expire after TICKET_TTL_SECONDS if unused.
        """
        ticket = str(uuid.uuid4())[:8]   # short 8-char token
        with self._ticket_lock:
            self._tickets[ticket] = {
                "video_path": video_path,
                "expires": time.time() + TICKET_TTL_SECONDS,
            }
        print(f"[VideoServer] Ticket created: {ticket} → {video_path}")
        return ticket

    def _claim_ticket(self, ticket: str) -> "str | None":
        """
        Claim and remove a ticket. Returns video_path or None if invalid/expired.
        """
        with self._ticket_lock:
            entry = self._tickets.pop(ticket, None)
        if entry is None:
            return None
        if time.time() > entry["expires"]:
            print(f"[VideoServer] Ticket expired: {ticket}")
            return None
        return entry["video_path"]

    def _purge_expired_tickets(self):
        """Background cleanup — called occasionally."""
        now = time.time()
        with self._ticket_lock:
            expired = [k for k, v in self._tickets.items() if now > v["expires"]]
            for k in expired:
                del self._tickets[k]
        if expired:
            print(f"[VideoServer] Purged {len(expired)} expired ticket(s)")

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self):
        """Block forever accepting clients. Call from a daemon thread."""
        try:
            self._create_server_socket()
            self.is_running = True
            print(f"[VideoServer] Listening on {self.host}:{self.port} (single port, multi-client)")
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

    # ── Private ────────────────────────────────────────────────────────────────

    def _create_server_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, SOCKET_REUSE_ADDRESS)
        s.bind((self.host, self.port))
        s.listen(MAX_PENDING_CONNECTIONS)
        self.server_socket = s

    def _accept_loop(self):
        purge_counter = 0
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
            except OSError:
                break
            except Exception as e:
                if self.is_running:
                    print(f"[VideoServer] Accept error: {e}")
                continue

            # Periodic ticket cleanup
            purge_counter += 1
            if purge_counter % 10 == 0:
                self._purge_expired_tickets()

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
        1. Receive 8-byte ticket from client.
        2. Look up which video to stream.
        3. Do key exchange.
        4. Stream via ClientHandler.
        """
        with self._client_lock:
            self.active_clients.append(address)

        print(f"[VideoServer] Client #{client_id} connected from {address}")

        try:
            # Step 1 – receive ticket (8 bytes, no encryption yet)
            ticket_bytes = self._recv_exact(client_socket, 8)
            if not ticket_bytes:
                print(f"[VideoServer] Client #{client_id} sent no ticket")
                return

            ticket = ticket_bytes.decode("utf-8", errors="replace")
            video_path = self._claim_ticket(ticket)

            if not video_path:
                print(f"[VideoServer] Invalid/expired ticket '{ticket}' from {address}")
                # Send a single '0' byte to signal rejection
                try:
                    client_socket.sendall(b'\x00')
                except Exception:
                    pass
                return

            # Signal acceptance
            try:
                client_socket.sendall(b'\x01')
            except Exception:
                return

            print(f"[VideoServer] Client #{client_id} ticket OK → {video_path}")

            # Step 2 – key exchange (server role: recv then send)
            conn = (client_socket, None)
            encryption_key = key_exchange.KeyExchange.recv_send_key(conn)
            encrypted_conn = (client_socket, encryption_key)

            # Step 3 – stream
            handler = ClientHandler(video_path, encrypted_conn, address, client_id)
            handler.handle_streaming()

        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError):
            pass
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

    @staticmethod
    def _recv_exact(sock: socket.socket, n: int) -> bytes:
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                return b""
            data += chunk
        return data

    def _teardown(self):
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass


# ── Module-level helpers used by Methods.py / Server.py ──────────────────────

def _get_or_create_server() -> VideoAudioServer:
    """Return the global singleton, starting it if needed."""
    global _server_instance, _server_thread
    with _server_lock:
        if _server_instance is not None and _server_instance.is_running:
            return _server_instance

        print(f"[VideoServer] Starting singleton on port {DEFAULT_PORT}...")
        srv = VideoAudioServer(DEFAULT_HOST, DEFAULT_PORT)
        thr = threading.Thread(
            target=srv.start,
            daemon=True,
            name="VideoServer-Main"
        )
        _server_instance = srv
        _server_thread = thr
        thr.start()
        # Give the socket a moment to bind
        time.sleep(0.2)
        print(f"[VideoServer] Singleton running on port {DEFAULT_PORT}")
        return srv


def ensure_video_server_running(video_path: str = "") -> dict:
    """
    Ensure the single streaming server is running.
    If video_path is provided, create a ticket for it.
    Returns {"server": <VideoAudioServer>, "port": DEFAULT_PORT, "ticket": <str|None>}
    """
    srv = _get_or_create_server()

    ticket = None
    if video_path:
        ticket = srv.create_ticket(video_path)

    return {
        "server": srv,
        "port": DEFAULT_PORT,
        "ticket": ticket,
    }


def run_video_player_server(video_path: str):
    """Legacy entry point kept for compatibility."""
    ensure_video_server_running(video_path)