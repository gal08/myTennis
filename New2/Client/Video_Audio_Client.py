"""
Gal Haham
Video & Audio Streaming Client - RECEIVE ONLY
FIXED: Client never sends data to server after key exchange.
ADDED: zlib decompression after AES decryption to match ClientHandler pipeline.
Pipeline: recv → AES decrypt → zlib decompress → pickle.loads → display
"""
import socket
import cv2
import pickle
import zlib
import threading
import pyaudio
import time
import aes_cipher
from Protocol import Protocol
from key_exchange import KeyExchange

DEFAULT_CLIENT_HOST = "127.0.0.1"
DEFAULT_CLIENT_PORT = 9999

WINDOW_POSITION_X = 100
WINDOW_POSITION_Y = 50
KEYBOARD_WAIT_MS = 1
KEY_MASK = 0xFF
KEY_ESCAPE = 27
WINDOW_VISIBLE_THRESHOLD = 1

MAX_RETRIES = 5
RETRY_DELAY = 1
CONNECT_TIMEOUT = 10

KEY_INDEX = 1


class VideoAudioClient:
    """
    Receive-only streaming client.
    Decryption + decompression pipeline mirrors ClientHandler in reverse.
    """

    def __init__(self, host: str = DEFAULT_CLIENT_HOST, port: int = DEFAULT_CLIENT_PORT):
        self.host = host
        self.port = port
        self.stream_info = None
        self.is_playing = False
        self.stop_flag = threading.Event()
        self.audio_stream = None
        self.pyaudio_instance = None
        self._compressed = False

        self.socket = self._connect_with_retry()

        print("[Client] Key exchange...")
        conn = (self.socket, None)
        self.encryption_key = KeyExchange.send_recv_key(conn)
        self.conn = (self.socket, self.encryption_key)
        print(f"[Client] Encryption ready ({len(self.encryption_key)} bytes)")

    def _connect_with_retry(self) -> socket.socket:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(f"[Client] Connecting to {self.host}:{self.port} (attempt {attempt}/{MAX_RETRIES})...")
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(CONNECT_TIMEOUT)
                s.connect((self.host, self.port))
                s.settimeout(None)
                print(f"[Client] Connected")
                return s
            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                if attempt < MAX_RETRIES:
                    print(f"[Client] Failed: {e}. Retry in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    raise ConnectionError(
                        f"Cannot connect to {self.host}:{self.port} after {MAX_RETRIES} attempts. Last error: {e}"
                    )

    def connect(self) -> bool:
        try:
            self._receive_stream_info()
            self._initialize_audio()
            return True
        except Exception as e:
            print(f"[Client] Setup failed: {e}")
            if self.socket:
                self.socket.close()
            return False

    def _receive_stream_info(self):
        obj = self._recv_decrypt_decompress()
        if obj is None:
            raise ConnectionError("No stream info received from server")
        self.stream_info = obj
        self._compressed = obj.get('compressed', False)
        print(f"[Client] Stream info:")
        print(f"  {self.stream_info['width']}x{self.stream_info['height']} @ {self.stream_info['fps']:.1f} fps")
        print(f"  Frames: {self.stream_info['total_frames']} | Audio: {self.stream_info['has_audio']} | Compressed: {self._compressed}")

    def _initialize_audio(self):
        if not (self.stream_info and self.stream_info.get('has_audio')):
            return
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.stream_info['audio_channels'],
                rate=self.stream_info['audio_sample_rate'],
                output=True,
                frames_per_buffer=self.stream_info['samples_per_frame']
            )
            print("[Client] Audio output ready")
        except Exception as e:
            print(f"[Client] Audio init failed: {e}")
            self.stream_info['has_audio'] = False

    def _recv_decrypt_decompress(self):
        """
        recv_bin → AES decrypt → zlib decompress → pickle.loads
        Exact reverse of ClientHandler._send_compressed_encrypted()
        """
        try:
            raw = Protocol.recv_bin(self.conn)
            if not raw:
                return None

            data = raw if isinstance(raw, bytes) else raw.encode()

            # 1. Decrypt
            if self.encryption_key:
                data = aes_cipher.AESCipher.decrypt(self.encryption_key, data)

            # 2. Decompress
            try:
                data = zlib.decompress(data)
            except zlib.error:
                pass  # Safety fallback if not compressed

            # 3. Deserialise
            return pickle.loads(data)

        except Exception as e:
            print(f"[Client] Receive error: {e}")
            return None

    def receive_packet(self):
        return self._recv_decrypt_decompress()

    def play_stream(self):
        if not self.stream_info:
            print("[Client] No stream info available")
            return

        win = "Video Stream"
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win, self.stream_info['width'], self.stream_info['height'])
        cv2.moveWindow(win, WINDOW_POSITION_X, WINDOW_POSITION_Y)

        self.is_playing = True
        frame_count = 0
        print("[Client] Playback started (Q or close window to stop)")

        while not self.stop_flag.is_set():
            packet = self.receive_packet()
            if packet is None:
                print("[Client] Stream ended")
                break

            cv2.imshow(win, packet['frame'])
            frame_count += 1

            if self.audio_stream and packet.get('audio') is not None:
                try:
                    self.audio_stream.write(packet['audio'].tobytes())
                except Exception:
                    pass

            key = cv2.waitKey(KEYBOARD_WAIT_MS) & KEY_MASK
            if key == ord('q') or key == KEY_ESCAPE:
                print("[Client] Stopped by user")
                break

            try:
                if cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < WINDOW_VISIBLE_THRESHOLD:
                    print("[Client] Window closed")
                    break
            except Exception:
                break

        self.is_playing = False
        cv2.destroyAllWindows()
        self.cleanup()
        print(f"[Client] Done. Received {frame_count} frames")

    def cleanup(self):
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception:
                pass
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except Exception:
                pass
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        print("[Client] Disconnected and cleaned up")