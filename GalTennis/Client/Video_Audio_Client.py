"""
Gal Haham
Video & Audio Streaming Client - ENCRYPTED VERSION
Handles connection, receiving stream data, and playback with full encryption
ENHANCED: Added Diffie-Hellman key exchange and AES decryption
FIXED: Added retry logic and better error handling
"""
import socket
import cv2
import pickle
import struct
import threading
import pyaudio
import numpy as np
import time
import key_exchange
import aes_cipher

DEFAULT_CLIENT_HOST = "127.0.0.1"
DEFAULT_CLIENT_PORT = 9999
NETWORK_HEADER_LENGTH_BYTES = 8
FIRST_TUPLE_INDEX = 0
WINDOW_POSITION_X = 100
WINDOW_POSITION_Y = 50
INITIAL_FRAME_COUNT = 0
FRAME_INCREMENT_STEP = 1
KEYBOARD_WAIT_TIME_MS = 1
KEY_CODE_MASK_8BIT = 0xFF
ESCAPE_KEY_CODE = 27
WINDOW_NOT_VISIBLE_THRESHOLD = 1
SOCK_INDEX = 0
KEY_INDEX = 1

MAX_CONNECTION_RETRIES = 5
RETRY_DELAY_SECONDS = 1
CONNECTION_TIMEOUT_SECONDS = 10

from Protocol import Protocol

class VideoAudioClient:

    def __init__(self, host=DEFAULT_CLIENT_HOST, port=DEFAULT_CLIENT_PORT):
        self.host = host
        self.port = port
        self.stream_info = None
        self.is_playing = False
        self.stop_flag = threading.Event()
        self.audio_stream = None
        self.pyaudio_instance = None
        self.socket = self._connect_with_retry()
        print("Performing key exchange...")
        temp_conn = (self.socket, None)
        encryption_key = key_exchange.KeyExchange.send_recv_key(temp_conn)
        self.conn = (self.socket, encryption_key)
        print(
            f"Encryption established (key length: {len(encryption_key)} bytes)")

    def _connect_with_retry(self):
        for attempt in range(MAX_CONNECTION_RETRIES):
            try:
                print(f"Connecting to {self.host}:{self.port} (attempt {attempt + 1}/{MAX_CONNECTION_RETRIES})...")

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(CONNECTION_TIMEOUT_SECONDS)

                sock.connect((self.host, self.port))

                print(f"✅ Connected to server {self.host}:{self.port}")
                return sock

            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                if attempt < MAX_CONNECTION_RETRIES - 1:
                    print(f"⚠️  Connection failed: {e}")
                    print(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    error_msg = (
                        f"Failed to connect to {self.host}:{self.port} "
                        f"after {MAX_CONNECTION_RETRIES} attempts. "
                        f"Last error: {e}"
                    )
                    raise ConnectionError(error_msg)

    def _receive_stream_info(self):
        encryption_key = self.conn[KEY_INDEX]

        info_data = Protocol.recv_bin(self.conn)

        if not info_data:
            raise ConnectionError("Failed to receive stream info data")

        if encryption_key:
            decrypted_data = aes_cipher.AESCipher.decrypt(
                encryption_key,
                info_data.encode() if isinstance(info_data, str) else info_data
            )
            self.stream_info = pickle.loads(decrypted_data)
        else:
            if isinstance(info_data, str):
                self.stream_info = pickle.loads(info_data.encode())
            else:
                self.stream_info = pickle.loads(info_data)

        print(f"Stream Info received (ENCRYPTED): ")
        print(
            f"   Video: {self.stream_info['width']}x"
            f"{self.stream_info['height']}"
        )
        print(f"   FPS: {self.stream_info['fps']:.2f}")
        print(f"   Frames: {self.stream_info['total_frames']}")
        print(f"   Has Audio: {self.stream_info['has_audio']}")
        return True

    def _initialize_audio(self):
        if self.stream_info and self.stream_info['has_audio']:
            try:
                self.pyaudio_instance = pyaudio.PyAudio()
                self.audio_stream = self.pyaudio_instance.open(
                    format=pyaudio.paInt16,
                    channels=self.stream_info['audio_channels'],
                    rate=self.stream_info['audio_sample_rate'],
                    output=True,
                    frames_per_buffer=self.stream_info['samples_per_frame']
                )
                print("Audio initialized")
            except Exception as e:
                print(f"Audio initialization failed: {e}")
                self.stream_info['has_audio'] = False
        return True

    def connect(self):
        try:
            self._receive_stream_info()
            self._initialize_audio()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            import traceback
            traceback.print_exc()
            if self.socket:
                self.socket.close()
            return False

    def recv_all(self, size):
        data = b''
        while len(data) < size:
            packet = self.socket.recv(size - len(data))
            if not packet:
                return None
            data += packet
        return data

    def receive_packet(self):
        try:
            packet_data = Protocol.recv_bin(self.conn)

            if not packet_data:
                return None

            encryption_key = self.conn[KEY_INDEX]
            if encryption_key:
                decrypted_data = aes_cipher.AESCipher.decrypt(
                    encryption_key,
                    packet_data.encode() if isinstance(packet_data, str) else packet_data
                )
                packet = pickle.loads(decrypted_data)
            else:
                if isinstance(packet_data, str):
                    packet = pickle.loads(packet_data.encode())
                else:
                    packet = pickle.loads(packet_data)

            return packet

        except Exception as e:
            print(f"Error receiving packet: {e}")
            return None

    def play_stream(self):
        if not self.stream_info:
            print("No stream info available")
            return

        window_name = "Encrypted Video & Audio Stream"
        self._setup_window(window_name)

        self.is_playing = True
        frame_count = INITIAL_FRAME_COUNT
        print("Playing encrypted video & audio stream...")

        while not self.stop_flag.is_set():
            packet = self.receive_packet()
            if packet is None:
                print("Stream ended")
                break

            frame_count = self._process_packet(
                window_name,
                packet,
                frame_count
            )

            if self._check_user_input(window_name):
                break

        self.is_playing = False
        self._teardown_window()
        self.cleanup()
        print(f"Received {frame_count} encrypted frames")

    def _setup_window(self, window_name):
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name,
                         self.stream_info['width'],
                         self.stream_info['height'])
        cv2.moveWindow(window_name, WINDOW_POSITION_X, WINDOW_POSITION_Y)

    def _process_packet(self, window_name, packet, frame_count):
        frame = packet['frame']
        cv2.imshow(window_name, frame)
        frame_count += FRAME_INCREMENT_STEP

        if self.audio_stream and packet['audio'] is not None:
            self._play_audio_chunk(packet['audio'])

        return frame_count

    def _play_audio_chunk(self, audio_chunk):
        try:
            audio_bytes = audio_chunk.tobytes()
            self.audio_stream.write(audio_bytes)
        except Exception as e:
            print(f"Audio playback error: {e}")

    @staticmethod
    def _check_user_input(window_name):
        key = cv2.waitKey(KEYBOARD_WAIT_TIME_MS) & KEY_CODE_MASK_8BIT

        if key == ord('q') or key == ESCAPE_KEY_CODE:
            print("Stopped by user")
            return True

        try:
            window_visible = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
            if window_visible < WINDOW_NOT_VISIBLE_THRESHOLD:
                print("Window closed")
                return True
        except:
            print("Window closed")
            return True

        return False

    @staticmethod
    def _teardown_window():
        cv2.destroyAllWindows()

    def cleanup(self):
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
        if self.socket:
            self.socket.close()
            print("Disconnected from server")
