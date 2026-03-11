"""
Gal Haham
Story player client - ENCRYPTED + COMPRESSED
FIXED: Uses Protocol.recv_bin instead of raw struct (matches server)
FIXED: Decompression pipeline: recv_bin → AES.decrypt → zlib.decompress → pickle
FIXED: Proper conn tuple passed everywhere
"""
import socket
import cv2
import pickle
import zlib
import pyaudio
import numpy as np
import key_exchange
import aes_cipher
from Protocol import Protocol

STORY_SERVER_HOST = "127.0.0.1"
STORY_SERVER_PORT = 6001

FRAME_INCREMENT = 1
MODULO_SUCCESS = 0
FPS_RATE = 30
FRAME_DELAY_MS = 1
KEY_ESCAPE = 27
IS_WINDOW_VISIBLE = 1
SOCK_INDEX = 0
KEY_INDEX = 1

TEXT_INFO_X = 10
TEXT_INFO_Y = 30
TEXT_AUDIO_STATUS_X = 10
TEXT_AUDIO_STATUS_Y = 60
TEXT_INSTRUCTIONS_X = 10
TEXT_INSTRUCTIONS_Y_OFFSET = 20

FONT_SIZE_INFO = 0.7
FONT_SIZE_AUDIO = 0.6
FONT_SIZE_INSTRUCTIONS = 0.6
LINE_THICKNESS = 2

COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)


class StoryPlayer:
    """
    Receive-only story player.
    Pipeline: Protocol.recv_bin → AES.decrypt → zlib.decompress → pickle.loads
    Mirrors story_player_server.py exactly.
    """

    def __init__(self, host: str = STORY_SERVER_HOST, port: int = STORY_SERVER_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.conn = None            # (socket, encryption_key)
        self.story_info = None
        self.audio_stream = None
        self.pyaudio_instance = None

    # ── Connection ─────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        try:
            print(f"[StoryClient] Connecting to {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print("[StoryClient] Connected")

            # Key exchange - client role
            temp_conn = (self.socket, None)
            key = key_exchange.KeyExchange.send_recv_key(temp_conn)
            self.conn = (self.socket, key)
            print(f"[StoryClient] Encryption ready ({len(key)} bytes)")

            # Receive story metadata
            self.story_info = self._recv_decrypt_decompress()
            if not self.story_info:
                print("[StoryClient] Failed to receive story info")
                return False

            self._print_story_info()

            if self.story_info.get('has_audio'):
                self._initialize_audio()

            return True

        except Exception as e:
            print(f"[StoryClient] Connection error: {e}")
            if self.socket:
                self.socket.close()
            return False

    # ── Core receive pipeline ─────────────────────────────────────────────────

    def _recv_decrypt_decompress(self):
        """
        Protocol.recv_bin → AES.decrypt → zlib.decompress → pickle.loads
        Exact reverse of StoryClientSession._send_compressed_encrypted()
        """
        try:
            raw = Protocol.recv_bin(self.conn)
            if not raw:
                return None

            # 1. Decrypt
            key = self.conn[KEY_INDEX]
            data = raw if isinstance(raw, bytes) else raw.encode()
            if key:
                data = aes_cipher.AESCipher.decrypt(key, data)

            # 2. Decompress
            try:
                data = zlib.decompress(data)
            except zlib.error:
                pass    # Fallback: not compressed

            # 3. Deserialise
            return pickle.loads(data)

        except Exception as e:
            print(f"[StoryClient] Receive error: {e}")
            return None

    # ── Audio ──────────────────────────────────────────────────────────────────

    def _initialize_audio(self):
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.story_info['audio_channels'],
                rate=self.story_info['audio_sample_rate'],
                output=True,
                frames_per_buffer=self.story_info['samples_per_frame']
            )
            print("[StoryClient] Audio ready")
        except Exception as e:
            print(f"[StoryClient] Audio init failed: {e}")
            self.story_info['has_audio'] = False

    # ── Playback ───────────────────────────────────────────────────────────────

    def play_story(self):
        if not self.story_info:
            print("[StoryClient] No story info")
            return

        win = f"Story - {self.story_info['type']}"
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win, self.story_info['width'], self.story_info['height'])

        frame_count = 0
        print(f"[StoryClient] Playing {self.story_info['type']} story...")

        while True:
            packet = self._recv_decrypt_decompress()
            if packet is None:
                print("[StoryClient] Story ended")
                break

            frame = packet['frame']
            self._add_overlay(frame, frame_count)
            cv2.imshow(win, frame)

            if self.audio_stream and packet.get('audio') is not None:
                try:
                    self.audio_stream.write(packet['audio'].tobytes())
                except Exception:
                    pass

            frame_count += FRAME_INCREMENT

            if frame_count % FPS_RATE == MODULO_SUCCESS:
                print(f"[StoryClient] Frame {frame_count}/{self.story_info['total_frames']}")

            key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
            if key == KEY_ESCAPE or key == ord('q') or key == ord('Q'):
                print("[StoryClient] Skipped by user")
                break

            try:
                if cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < IS_WINDOW_VISIBLE:
                    print("[StoryClient] Window closed")
                    break
            except Exception:
                break

        cv2.destroyAllWindows()
        self.cleanup()
        print(f"[StoryClient] Done ({frame_count} frames)")

    # ── Overlay text ───────────────────────────────────────────────────────────

    def _add_overlay(self, frame, frame_count: int):
        cv2.putText(
            frame,
            f"{self.story_info['type']} | Frame {frame_count + 1}/{self.story_info['total_frames']}",
            (TEXT_INFO_X, TEXT_INFO_Y),
            cv2.FONT_HERSHEY_SIMPLEX, FONT_SIZE_INFO, COLOR_WHITE, LINE_THICKNESS
        )
        has_audio = self.story_info.get('has_audio') and self.audio_stream
        cv2.putText(
            frame,
            "Audio: ON" if has_audio else "Audio: OFF",
            (TEXT_AUDIO_STATUS_X, TEXT_AUDIO_STATUS_Y),
            cv2.FONT_HERSHEY_SIMPLEX, FONT_SIZE_AUDIO,
            COLOR_GREEN if has_audio else COLOR_RED, LINE_THICKNESS
        )
        cv2.putText(
            frame,
            "Press Q or ESC to skip",
            (TEXT_INSTRUCTIONS_X, self.story_info['height'] - TEXT_INSTRUCTIONS_Y_OFFSET),
            cv2.FONT_HERSHEY_SIMPLEX, FONT_SIZE_INSTRUCTIONS, COLOR_YELLOW, LINE_THICKNESS
        )

    def _print_story_info(self):
        print(f"[StoryClient] Story info:")
        print(f"  Type: {self.story_info['type']}")
        print(f"  {self.story_info['width']}x{self.story_info['height']} @ {self.story_info['fps']:.1f} fps")
        print(f"  Frames: {self.story_info['total_frames']} | Audio: {self.story_info.get('has_audio')} | Compressed: {self.story_info.get('compressed')}")

    # ── Cleanup ────────────────────────────────────────────────────────────────

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
        print("[StoryClient] Disconnected")


def run_story_player_client(host: str = STORY_SERVER_HOST, port: int = STORY_SERVER_PORT):
    player = StoryPlayer(host, port)
    if player.connect():
        player.play_story()
    else:
        print("[StoryClient] Failed to connect")


if __name__ == '__main__':
    run_story_player_client()