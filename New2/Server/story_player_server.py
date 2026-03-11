"""
Gal Haham
Story streaming server for images and videos - ENCRYPTED + COMPRESSED
FIXED: Multi-client support - accepts clients in a loop forever
FIXED: No timeout - waits indefinitely for clients
ADDED: zlib compression before encryption (same pipeline as ClientHandler)
Pipeline: pickle → zlib.compress → AES.encrypt → Protocol.send_bin
"""
import socket
import os
import cv2
import time
import pickle
import zlib
import threading
import subprocess
import numpy as np
import key_exchange
import aes_cipher
from Protocol import Protocol

STORY_SERVER_HOST = '0.0.0.0'
STORY_SERVER_PORT = 6001
STORY_FOLDER = "stories"
MAX_SPLIT_COUNT = 1
DEFAULT_AUDIO_SAMPLE_RATE = 44100
DEFAULT_AUDIO_CHANNELS = 2
DESIRED_JPEG_QUALITY = 80
FRAME_RATE_FPS = 30
ZERO_REMAINDER = 0
DEFAULT_FPS = 30.0
MAXIMUM_FPS_LIMIT = 60
MINIMUM_FPS_LIMIT = 0
SECONDS_IN_ONE_UNIT = 1.0
BYTES_PER_SAMPLE_16_BIT = 2
INITIAL_COUNT = 0
TARGET_FRAME_HEIGHT = 480
TARGET_FRAME_WIDTH = 640
STORY_TOTAL_FRAME_COUNT = 150
LARGE_IO_BUFFER_SIZE_BYTES = 100_000_000
INCREMENT_STEP = 1
TARGET_FPS = 30
MINIMUM_DELAY_SECONDS = 0
SOCKET_OPTION_ENABLED = 1
MAX_PENDING_CONNECTIONS = 10
FILE_EXTENSION_INDEX = 1
SOCK_INDEX = 0
KEY_INDEX = 1
COMPRESS_LEVEL = 1      # zlib level 1 = fastest, good for streaming


class StoryClientSession:
    """Handles a single connected client - runs in its own thread."""

    def __init__(self, client_socket: socket.socket, addr: tuple, session_id: int):
        self.client_socket = client_socket
        self.addr = addr
        self.session_id = session_id
        self.encrypted_conn = None

    # ── Core send pipeline ─────────────────────────────────────────────────────

    def _send_compressed_encrypted(self, obj) -> bool:
        """pickle → zlib.compress → AES.encrypt → Protocol.send_bin"""
        try:
            raw = pickle.dumps(obj)
            compressed = zlib.compress(raw, level=COMPRESS_LEVEL)
            encryption_key = self.encrypted_conn[KEY_INDEX]
            if encryption_key:
                payload = aes_cipher.AESCipher.encrypt(encryption_key, compressed)
            else:
                payload = compressed
            Protocol.send_bin(payload, self.encrypted_conn)
            return True
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            return False
        except Exception as e:
            print(f"[StoryServer #{self.session_id}] Send error: {e}")
            return False

    # ── Key exchange ───────────────────────────────────────────────────────────

    def establish_encryption(self) -> bool:
        try:
            temp_conn = (self.client_socket, None)
            key = key_exchange.KeyExchange.recv_send_key(temp_conn)
            self.encrypted_conn = (self.client_socket, key)
            print(f"[StoryServer #{self.session_id}] Encryption ready ({len(key)} bytes)")
            return True
        except Exception as e:
            print(f"[StoryServer #{self.session_id}] Key exchange failed: {e}")
            return False

    # ── Story dispatching ──────────────────────────────────────────────────────

    def stream_story(self, story_path: str):
        ext = os.path.splitext(story_path)[FILE_EXTENSION_INDEX].lower()
        is_image = ext in ['.jpg', '.jpeg', '.png', '.bmp']
        is_video = ext in ['.mp4', '.avi', '.mov', '.mkv']

        if is_image:
            self._send_image_story(story_path)
        elif is_video:
            self._send_video_story(story_path)
        else:
            print(f"[StoryServer #{self.session_id}] Unsupported format: {ext}")

    # ── Image story ────────────────────────────────────────────────────────────

    def _send_image_story(self, image_path: str):
        img = cv2.imread(image_path)
        if img is None:
            print(f"[StoryServer #{self.session_id}] Cannot read image")
            return

        img = cv2.resize(img, (TARGET_FRAME_WIDTH, TARGET_FRAME_HEIGHT))

        story_info = {
            'type': 'IMAGE',
            'width': TARGET_FRAME_WIDTH,
            'height': TARGET_FRAME_HEIGHT,
            'fps': DEFAULT_FPS,
            'total_frames': STORY_TOTAL_FRAME_COUNT,
            'has_audio': False,
            'compressed': True,
        }

        if not self._send_compressed_encrypted(story_info):
            return

        print(f"[StoryServer #{self.session_id}] Sending {STORY_TOTAL_FRAME_COUNT} image frames...")
        frame_delay = SECONDS_IN_ONE_UNIT / DEFAULT_FPS

        for i in range(STORY_TOTAL_FRAME_COUNT):
            packet = {'frame': img, 'audio': None, 'frame_number': i}
            if not self._send_compressed_encrypted(packet):
                return
            time.sleep(frame_delay)

        print(f"[StoryServer #{self.session_id}] Image story done")

    # ── Video story ────────────────────────────────────────────────────────────

    def _send_video_story(self, video_path: str):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"[StoryServer #{self.session_id}] Cannot open video")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not (MINIMUM_FPS_LIMIT < fps <= MAXIMUM_FPS_LIMIT):
            fps = DEFAULT_FPS
        frame_delay = SECONDS_IN_ONE_UNIT / fps
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        audio_info = self._get_audio_info(video_path)
        samples_per_frame = int(audio_info['sample_rate'] / fps)
        chunk_bytes = samples_per_frame * audio_info['channels'] * BYTES_PER_SAMPLE_16_BIT
        audio_proc = self._start_audio_process(video_path, audio_info)

        story_info = {
            'type': 'VIDEO',
            'width': width,
            'height': height,
            'fps': fps,
            'total_frames': total_frames,
            'has_audio': audio_proc is not None,
            'audio_sample_rate': audio_info['sample_rate'],
            'audio_channels': audio_info['channels'],
            'samples_per_frame': samples_per_frame,
            'compressed': True,
        }

        if not self._send_compressed_encrypted(story_info):
            self._cleanup_video(cap, audio_proc)
            return

        print(f"[StoryServer #{self.session_id}] Streaming video story...")
        frame_count = INITIAL_COUNT

        while True:
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (TARGET_FRAME_WIDTH, TARGET_FRAME_HEIGHT))
            audio_chunk = self._read_audio(audio_proc, chunk_bytes)

            packet = {'frame': frame, 'audio': audio_chunk, 'frame_number': frame_count}
            if not self._send_compressed_encrypted(packet):
                break

            frame_count += INCREMENT_STEP
            if frame_count % TARGET_FPS == ZERO_REMAINDER:
                print(f"[StoryServer #{self.session_id}] Frame {frame_count}/{total_frames}")

            elapsed = time.time() - t0
            sleep_time = max(MINIMUM_DELAY_SECONDS, frame_delay - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

        self._cleanup_video(cap, audio_proc)
        print(f"[StoryServer #{self.session_id}] Video story done ({frame_count} frames)")

    # ── Audio helpers ──────────────────────────────────────────────────────────

    def _get_audio_info(self, video_path: str) -> dict:
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                 '-show_entries', 'stream=sample_rate,channels',
                 '-of', 'default=noprint_wrappers=1', video_path],
                capture_output=True, text=True, check=True
            )
            info = {}
            for line in result.stdout.splitlines():
                if '=' in line:
                    k, v = line.split('=', MAX_SPLIT_COUNT)
                    info[k.strip()] = v.strip()
            return {
                'sample_rate': int(info.get('sample_rate', DEFAULT_AUDIO_SAMPLE_RATE)),
                'channels': int(info.get('channels', DEFAULT_AUDIO_CHANNELS)),
            }
        except Exception:
            return {'sample_rate': DEFAULT_AUDIO_SAMPLE_RATE, 'channels': DEFAULT_AUDIO_CHANNELS}

    def _start_audio_process(self, video_path: str, audio_info: dict):
        try:
            return subprocess.Popen(
                ['ffmpeg', '-i', video_path, '-vn',
                 '-acodec', 'pcm_s16le',
                 '-ar', str(audio_info['sample_rate']),
                 '-ac', str(audio_info['channels']),
                 '-f', 's16le', 'pipe:1'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=LARGE_IO_BUFFER_SIZE_BYTES
            )
        except Exception:
            return None

    def _read_audio(self, audio_proc, chunk_bytes):
        if audio_proc and audio_proc.stdout:
            try:
                data = audio_proc.stdout.read(chunk_bytes)
                if data and len(data) == chunk_bytes:
                    return np.frombuffer(data, dtype=np.int16)
            except Exception:
                pass
        return None

    def _cleanup_video(self, cap, audio_proc):
        try:
            cap.release()
        except Exception:
            pass
        if audio_proc:
            try:
                audio_proc.terminate()
                audio_proc.wait()
            except Exception:
                pass

    def close(self):
        try:
            self.client_socket.close()
        except Exception:
            pass


# ── Persistent multi-client server ────────────────────────────────────────────

class StoryPlayerServer:
    """
    Persistent story streaming server.
    Runs forever, accepts multiple clients concurrently.
    Each client gets its own thread.
    Each story gets its own port (assigned by Methods.py).
    """

    def __init__(self, story_filename: str,
                 host: str = STORY_SERVER_HOST,
                 port: int = STORY_SERVER_PORT):
        self.story_filename = story_filename
        self.story_path = os.path.join(STORY_FOLDER, story_filename)
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self._client_counter = 0
        self._counter_lock = threading.Lock()
        self._ready_event = threading.Event()   # fires when socket is listening

    def wait_until_ready(self, timeout=5.0):
        """Block until the server socket is actually listening."""
        return self._ready_event.wait(timeout)

    def start(self):
        """Start server and accept clients forever."""
        if not os.path.exists(self.story_path):
            print(f"[StoryServer] File not found: {self.story_path}")
            return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, SOCKET_OPTION_ENABLED
        )
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MAX_PENDING_CONNECTIONS)
        self.is_running = True
        self._ready_event.set()             # signal: ready to accept

        print(f"[StoryServer] Listening on {self.host}:{self.port}")
        print(f"[StoryServer] Story: {self.story_filename}")

        while self.is_running:
            try:
                # Blocking accept - no timeout, waits forever
                client_socket, addr = self.server_socket.accept()

                with self._counter_lock:
                    self._client_counter += 1
                    session_id = self._client_counter

                print(f"[StoryServer] Client #{session_id} connected from {addr}")

                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr, session_id),
                    daemon=True,
                    name=f"StoryClient-{session_id}"
                ).start()

            except OSError:
                if self.is_running:
                    print("[StoryServer] Socket error")
                break
            except Exception as e:
                if self.is_running:
                    print(f"[StoryServer] Accept error: {e}")

    def _handle_client(self, client_socket: socket.socket, addr: tuple, session_id: int):
        session = StoryClientSession(client_socket, addr, session_id)
        try:
            if not session.establish_encryption():
                return
            session.stream_story(self.story_path)
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError):
            pass  # Normal disconnect
        except Exception as e:
            print(f"[StoryServer #{session_id}] Error: {e}")
        finally:
            session.close()
            print(f"[StoryServer #{session_id}] Disconnected")

    def stop(self):
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass


def run_story_player_server(story_filename: str):
    server = StoryPlayerServer(story_filename)
    server.start()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        run_story_player_server(sys.argv[1])
    else:
        print("Usage: python story_player_server.py <story_filename>")