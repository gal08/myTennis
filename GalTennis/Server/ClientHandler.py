"""
Gal Haham
Client Handler - handles a single streaming client session
ADDED: zlib compression before encryption → smaller packets → faster transfer
CHANGED: DEFAULT_FPS capped at 20 for better cross-network performance
Compression pipeline: raw data → zlib.compress → AES.encrypt → send
"""
import pickle
import time
import cv2
import subprocess
import numpy as np
import zlib
import aes_cipher
from Protocol import Protocol

# ── Compression ───────────────────────────────────────────────────────────────
COMPRESS_LEVEL = 1          # zlib level 1 = fastest

# ── Video constants ───────────────────────────────────────────────────────────
DEFAULT_FPS = 20.0          # Capped at 20 for reliable cross-network streaming
MAXIMUM_FPS = 20.0          # Hard cap — prevents overwhelming slow connections
MINIMUM_FPS = 5.0
MINIMUM_DELAY = 0.0
JPEG_QUALITY = 75           # Slightly lower quality = smaller packets
LOG_INTERVAL_FRAMES = 30
LARGE_BUFFER = 100_000_000
BYTES_PER_SAMPLE = 2        # 16-bit PCM

KEY_INDEX = 1


class ClientHandler:
    """
    Handles one streaming client:
      1. Sends stream_info (compressed + encrypted)
      2. Loops: read frame → compress → encrypt → send
    """

    def __init__(self, video_path: str, conn: tuple, address: tuple, client_id: int):
        self.video_path = video_path
        self.conn = conn                    # (socket, encryption_key)
        self.address = address
        self.client_id = client_id
        self._encryption_key = conn[KEY_INDEX]

    # ── Public entry point ────────────────────────────────────────────────────

    def handle_streaming(self):
        cap = self._open_capture()
        if cap is None:
            return

        props = self._get_video_props(cap)
        audio_info = self._get_audio_info()
        audio_proc, samples_per_frame, chunk_bytes = self._start_audio(audio_info, props['fps'])

        stream_info = self._build_stream_info(props, audio_info, samples_per_frame, audio_proc)
        if not self._send_compressed_encrypted(stream_info):
            self._cleanup(cap, audio_proc)
            return

        print(f"[ClientHandler #{self.client_id}] Streaming {self.video_path} → {self.address} @ {props['fps']:.0f} fps")
        self._stream_loop(cap, props, audio_proc, chunk_bytes)
        self._cleanup(cap, audio_proc)

    # ── Setup helpers ─────────────────────────────────────────────────────────

    def _open_capture(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"[ClientHandler #{self.client_id}] Cannot open: {self.video_path}")
            return None
        return cap

    def _get_video_props(self, cap) -> dict:
        fps = cap.get(cv2.CAP_PROP_FPS)
        # Clamp to [MINIMUM_FPS, MAXIMUM_FPS]
        if not (MINIMUM_FPS <= fps <= MAXIMUM_FPS):
            fps = DEFAULT_FPS
        else:
            fps = min(fps, MAXIMUM_FPS)   # also cap if video is e.g. 30/60 fps
        return {
            'fps': fps,
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'frame_delay': 1.0 / fps,
        }

    def _get_audio_info(self) -> dict:
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                 '-show_entries', 'stream=sample_rate,channels',
                 '-of', 'default=noprint_wrappers=1', self.video_path],
                capture_output=True, text=True, check=True
            )
            info = {}
            for line in result.stdout.splitlines():
                if '=' in line:
                    k, v = line.split('=', 1)
                    info[k.strip()] = v.strip()
            return {
                'sample_rate': int(info.get('sample_rate', 44100)),
                'channels': int(info.get('channels', 2)),
            }
        except Exception:
            return {'sample_rate': 44100, 'channels': 2}

    def _start_audio(self, audio_info: dict, fps: float):
        samples_per_frame = int(audio_info['sample_rate'] / fps)
        chunk_bytes = samples_per_frame * audio_info['channels'] * BYTES_PER_SAMPLE
        try:
            proc = subprocess.Popen(
                ['ffmpeg', '-i', self.video_path, '-vn',
                 '-acodec', 'pcm_s16le',
                 '-ar', str(audio_info['sample_rate']),
                 '-ac', str(audio_info['channels']),
                 '-f', 's16le', 'pipe:1'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=LARGE_BUFFER
            )
            return proc, samples_per_frame, chunk_bytes
        except Exception:
            return None, samples_per_frame, chunk_bytes

    def _build_stream_info(self, props, audio_info, samples_per_frame, audio_proc) -> dict:
        return {
            'width': props['width'],
            'height': props['height'],
            'fps': props['fps'],
            'total_frames': props['total_frames'],
            'has_audio': audio_proc is not None,
            'audio_sample_rate': audio_info['sample_rate'],
            'audio_channels': audio_info['channels'],
            'samples_per_frame': samples_per_frame,
            'compressed': True,
        }

    # ── Streaming loop ────────────────────────────────────────────────────────

    def _stream_loop(self, cap, props, audio_proc, chunk_bytes):
        frame_count = 0
        start_time = time.time()

        while True:
            t0 = time.time()

            ret, frame = cap.read()
            if not ret:
                break

            audio_chunk = self._read_audio(audio_proc, chunk_bytes)

            packet = {
                'frame': frame,
                'audio': audio_chunk,
                'frame_number': frame_count,
            }

            if not self._send_compressed_encrypted(packet):
                break

            frame_count += 1

            if frame_count % LOG_INTERVAL_FRAMES == 0:
                elapsed = time.time() - start_time
                print(
                    f"[ClientHandler #{self.client_id}] "
                    f"Frame {frame_count}/{props['total_frames']} "
                    f"({elapsed:.1f}s)"
                )

            self._pace(t0, props['frame_delay'])

        print(f"[ClientHandler #{self.client_id}] Stream finished after {frame_count} frames")

    # ── Core: compress → encrypt → send ──────────────────────────────────────

    def _send_compressed_encrypted(self, obj) -> bool:
        try:
            raw = pickle.dumps(obj)
            compressed = zlib.compress(raw, level=COMPRESS_LEVEL)
            if self._encryption_key:
                payload = aes_cipher.AESCipher.encrypt(self._encryption_key, compressed)
            else:
                payload = compressed

            Protocol.send_bin(payload, self.conn)
            return True
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            return False
        except Exception as e:
            print(f"[ClientHandler #{self.client_id}] Send error: {e}")
            return False

    # ── Audio helper ──────────────────────────────────────────────────────────

    def _read_audio(self, audio_proc, chunk_bytes):
        if audio_proc and audio_proc.stdout:
            try:
                data = audio_proc.stdout.read(chunk_bytes)
                if data and len(data) == chunk_bytes:
                    return np.frombuffer(data, dtype=np.int16)
            except Exception:
                pass
        return None

    # ── Frame-rate pacing ─────────────────────────────────────────────────────

    @staticmethod
    def _pace(frame_start: float, frame_delay: float):
        sleep_time = frame_delay - (time.time() - frame_start)
        if sleep_time > MINIMUM_DELAY:
            time.sleep(sleep_time)

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def _cleanup(self, cap, audio_proc):
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