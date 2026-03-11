"""
Gal Haham
Story Player Server
REFACTORED: Single port (6001) for ALL stories, multithreaded clients.
            Ticket-based routing — same pattern as VideoAudioServer.
            Each PLAY_STORY request creates a short-lived ticket;
            the client sends the ticket on connect so the server
            knows which story file to stream.
"""
import socket
import os
import time
import threading
import uuid

from Story_client_session import StoryClientSession

STORY_SERVER_HOST = '0.0.0.0'
STORY_SERVER_PORT = 6001
STORY_FOLDER = "stories"

TICKET_TTL_SECONDS = 30
TICKET_LENGTH = 8
TICKET_ACCEPT = b'\x01'
TICKET_REJECT = b'\x00'

SOCKET_OPTION_ENABLED = 1
MAX_PENDING_CONNECTIONS = 20


class StoryPlayerServer:
    """
    Single persistent story streaming server on one fixed port (6001).
    All story play requests share this server.
    Each request creates a ticket; the client sends the ticket on connect
    so the server knows which story file to stream.
    """

    _instance: "StoryPlayerServer | None" = None
    _thread:   "threading.Thread | None" = None
    _lock = threading.Lock()

    def __init__(self, host: str = STORY_SERVER_HOST, port: int = STORY_SERVER_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self._client_counter = 0
        self._counter_lock = threading.Lock()

        # ticket_id → {"story_path": str, "expires": float}
        self._tickets: dict = {}
        self._ticket_lock = threading.Lock()

    # ── Singleton ─────────────────────────────────────────────────────────────

    @classmethod
    def get_or_create(cls) -> "StoryPlayerServer":
        """Return the global singleton, starting it if needed."""
        with cls._lock:
            if cls._instance is not None and cls._instance.is_running:
                return cls._instance

            print(f"[StoryServer] Starting singleton on port {STORY_SERVER_PORT}...")
            srv = cls(STORY_SERVER_HOST, STORY_SERVER_PORT)
            thr = threading.Thread(
                target=srv.start,
                daemon=True,
                name="StoryServer-Main"
            )
            cls._instance = srv
            cls._thread = thr
            thr.start()
            time.sleep(0.2)
            print(f"[StoryServer] Singleton running on port {STORY_SERVER_PORT}")
            return srv

    @classmethod
    def ensure_running(cls, story_path: str = "") -> dict:
        """
        Ensure the single story streaming server is running.
        If story_path is given, create a ticket for it.
        Returns {"server": ..., "port": STORY_SERVER_PORT, "ticket": <str|None>}
        """
        srv = cls.get_or_create()
        ticket = srv.create_ticket(story_path) if story_path else None
        return {
            "server": srv,
            "port": STORY_SERVER_PORT,
            "ticket": ticket,
        }

    @classmethod
    def run_legacy(cls, story_filename: str):
        """Legacy entry point kept for compatibility."""
        story_path = os.path.join(STORY_FOLDER, story_filename)
        cls.ensure_running(story_path)

    # ── Ticket API ────────────────────────────────────────────────────────────

    def create_ticket(self, story_path: str) -> str:
        """
        Create a one-time ticket for streaming a specific story.
        Returns an 8-char token the client must send on connect.
        """
        ticket = str(uuid.uuid4())[:TICKET_LENGTH]
        with self._ticket_lock:
            self._tickets[ticket] = {
                "story_path": story_path,
                "expires": time.time() + TICKET_TTL_SECONDS,
            }
        print(f"[StoryServer] Ticket created: {ticket} → {story_path}")
        return ticket

    def _claim_ticket(self, ticket: str) -> "str | None":
        """Claim and remove a ticket. Returns story_path or None."""
        with self._ticket_lock:
            entry = self._tickets.pop(ticket, None)
        if entry is None:
            return None
        if time.time() > entry["expires"]:
            print(f"[StoryServer] Ticket expired: {ticket}")
            return None
        return entry["story_path"]

    def _purge_expired_tickets(self):
        now = time.time()
        with self._ticket_lock:
            expired = [k for k, v in self._tickets.items() if now > v["expires"]]
            for k in expired:
                del self._tickets[k]
        if expired:
            print(f"[StoryServer] Purged {len(expired)} expired ticket(s)")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        """Block forever accepting clients. Call from a daemon thread."""
        try:
            self._create_server_socket()
            self.is_running = True
            print(f"[StoryServer] Listening on {self.host}:{self.port} (single port, multi-client)")
            self._accept_loop()
        except Exception as e:
            print(f"[StoryServer] Fatal: {e}")
        finally:
            self._teardown()

    def stop(self):
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        print("[StoryServer] Stopped")

    # ── Private ───────────────────────────────────────────────────────────────

    def _create_server_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, SOCKET_OPTION_ENABLED)
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
                    print(f"[StoryServer] Accept error: {e}")
                continue

            purge_counter += 1
            if purge_counter % 10 == 0:
                self._purge_expired_tickets()

            with self._counter_lock:
                self._client_counter += 1
                session_id = self._client_counter

            t = threading.Thread(
                target=self._handle_client,
                args=(client_socket, address, session_id),
                daemon=True,
                name=f"StoryClient-{session_id}"
            )
            t.start()

    def _handle_client(self, client_socket: socket.socket, address: tuple, session_id: int):
        """
        1. Receive 8-byte ticket.
        2. Look up story path.
        3. Key exchange.
        4. Stream story.
        """
        print(f"[StoryServer] Client #{session_id} connected from {address}")
        try:
            ticket_bytes = self._recv_exact(client_socket, TICKET_LENGTH)
            if not ticket_bytes:
                print(f"[StoryServer] Client #{session_id} sent no ticket")
                return

            ticket = ticket_bytes.decode("utf-8", errors="replace").rstrip('\x00')
            story_path = self._claim_ticket(ticket)

            if not story_path:
                print(f"[StoryServer] Invalid/expired ticket '{ticket}' from {address}")
                try:
                    client_socket.sendall(TICKET_REJECT)
                except Exception:
                    pass
                return

            try:
                client_socket.sendall(TICKET_ACCEPT)
            except Exception:
                return

            print(f"[StoryServer] Client #{session_id} ticket OK → {story_path}")

            session = StoryClientSession(client_socket, address, session_id)
            if not session.establish_encryption():
                return

            session.stream_story(story_path)

        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError):
            pass
        except Exception as e:
            print(f"[StoryServer] Client #{session_id} error: {e}")
        finally:
            print(f"[StoryServer] Client #{session_id} disconnected")
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


# ── Backward-compatible module-level wrappers ─────────────────────────────────

def ensure_story_server_running(story_path: str = "") -> dict:
    return StoryPlayerServer.ensure_running(story_path)


def run_story_player_server(story_filename: str):
    StoryPlayerServer.run_legacy(story_filename)