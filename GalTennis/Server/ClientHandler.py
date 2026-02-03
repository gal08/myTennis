"""
Gal Haham
Client Handler
Manages individual client streaming sessions with encryption
FIXED: Direct socket communication WITHOUT NetworkManager dependency
FIXED: Now uses Protocol.send() for consistency with client
FIXED: Silent error handling for client disconnections
"""
import time
import pickle
import struct
import aes_cipher
from VideoStreamManager import VideoStreamManager
from AudioStreamManager import AudioStreamManager
from Protocol import Protocol

INITIAL_FRAME_COUNT = 0
FRAME_INCREMENT_STEP = 1
SOCK_INDEX = 0
KEY_INDEX = 1
STRUCT_FORMAT_LONG = "!L"


class ClientHandler:

    def __init__(self, video_path, encrypted_conn, address, client_number=0):
        self.video_path = video_path
        self.encrypted_conn = encrypted_conn
        self.client_socket = encrypted_conn[SOCK_INDEX]
        self.encryption_key = encrypted_conn[KEY_INDEX]
        self.address = address
        self.client_number = client_number

        self.video_manager = VideoStreamManager(video_path)
        self.audio_manager = AudioStreamManager(video_path)

    def handle_streaming(self):
        try:
            print(f"[Client #{self.client_number}] === STARTING STREAMING ===")

            print(f"[Client #{self.client_number}] Step 1: Opening video...")
            if not self.video_manager.open_video():
                self._close_socket()
                return

            video_info = self.video_manager.get_video_info()
            print(f"[Client #{self.client_number}] Video opened: {video_info['width']}x{video_info['height']}")

            print(f"[Client #{self.client_number}] Step 2: Setting up audio...")
            self.audio_manager.setup_audio_extraction(video_info['fps'])

            print(f"[Client #{self.client_number}] Step 3: Sending stream info...")
            self._send_handshake(video_info)

            print(f"[Client #{self.client_number}] Step 4: Starting frame streaming...")
            self._stream_loop(video_info)

        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError):
            # Client disconnected - silent handling (no error messages)
            pass
        except Exception:
            # Suppress all other errors silently
            pass
        finally:
            self._cleanup()

    def _send_handshake(self, video_info):
        audio_info = self.audio_manager.get_audio_info()

        stream_info = {
            'fps': video_info['fps'],
            'width': video_info['width'],
            'height': video_info['height'],
            'total_frames': video_info['total_frames'],
            'audio_sample_rate': audio_info['audio_sample_rate'],
            'audio_channels': audio_info['audio_channels'],
            'samples_per_frame': audio_info['samples_per_frame'],
            'has_audio': audio_info['has_audio']
        }

        print(f"[Client #{self.client_number}] Preparing to send stream info...")

        try:
            self._send_stream_info_encrypted(stream_info)
            print(f"[Client #{self.client_number}] Stream info successfully sent!")
        except Exception:
            # Suppress send errors
            raise

        print(f"[Client #{self.client_number}] Streaming to {self.address} (ENCRYPTED)")
        print(
            f"[Client #{self.client_number}]    Video: {video_info['width']}x{video_info['height']} "
            f"@ {video_info['fps']:.2f} FPS"
        )
        print(
            f"[Client #{self.client_number}]    Audio: {audio_info['audio_sample_rate']} Hz, "
            f"{audio_info['audio_channels']} ch"
        )

    def _send_stream_info_encrypted(self, stream_info: dict):
        info_data = pickle.dumps(stream_info)

        if self.encryption_key:
            encrypted_data = aes_cipher.AESCipher.encrypt(
                self.encryption_key,
                info_data
            )
        else:
            encrypted_data = info_data

        Protocol.send_bin(encrypted_data, self.encrypted_conn)

    def _send_frame_packet(self, frame, audio_chunk, frame_number):
        packet = {
            'frame': frame,
            'audio': audio_chunk,
            'frame_number': frame_number
        }

        packet_data = pickle.dumps(packet)

        if self.encryption_key:
            encrypted_data = aes_cipher.AESCipher.encrypt(
                self.encryption_key,
                packet_data
            )
        else:
            encrypted_data = packet_data

        Protocol.send_bin(encrypted_data, self.encrypted_conn)

    def _stream_loop(self, video_info):
        streaming_state = self._initialize_streaming_state(video_info)

        print(f"[Client #{self.client_number}] Starting frame loop...")

        while True:
            if not self._process_single_frame(streaming_state):
                break

            streaming_state['frame_count'] += FRAME_INCREMENT_STEP

        print(f"[Client #{self.client_number}] Frame loop completed")

    def _initialize_streaming_state(self, video_info):
        return {
            'frame_count': INITIAL_FRAME_COUNT,
            'start_time': time.time(),
            'frame_delay': video_info['frame_delay'],
            'total_frames': video_info['total_frames']
        }

    def _process_single_frame(self, state):
        frame_start = time.time()

        ret, frame = self._read_video_frame()
        if not ret:
            self._print_stream_completion(state['frame_count'])
            return False

        audio_chunk = self._read_audio_chunk()

        try:
            self._send_frame_packet(frame, audio_chunk, state['frame_count'])
        except Exception:
            # Suppress send errors
            return False

        self._log_streaming_progress(state)

        self._control_frame_timing(frame_start, state['frame_delay'])

        return True

    def _read_video_frame(self):
        return self.video_manager.read_frame()

    def _read_audio_chunk(self):
        return self.audio_manager.read_audio_chunk()

    def _print_stream_completion(self, frame_count):
        print(
            f"[Client #{self.client_number}] Finished streaming to {self.address} "
            f"({frame_count} frames)"
        )

    def _log_streaming_progress(self, state):
        VideoStreamManager.log_progress(
            state['frame_count'],
            state['total_frames'],
            state['start_time'],
            self.address
        )

    def _control_frame_timing(self, frame_start, frame_delay):
        VideoStreamManager.control_frame_rate(frame_start, frame_delay)

    def _close_socket(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                # Suppress socket close errors
                pass

    def _cleanup(self):
        try:
            self.video_manager.close()
        except Exception:
            pass

        try:
            self.audio_manager.close()
        except Exception:
            pass

        self._close_socket()