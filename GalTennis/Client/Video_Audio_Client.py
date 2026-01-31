"""
Gal Haham
Video & Audio Streaming Client - ENCRYPTED VERSION
Handles connection, receiving stream data, and playback with full encryption
ENHANCED: Added Diffie-Hellman key exchange and AES decryption
"""
import socket
import cv2
import pickle
import struct
import threading
import pyaudio
import numpy as np
import key_exchange
import aes_cipher

DEFAULT_CLIENT_HOST = "127.0.0.1"
DEFAULT_CLIENT_PORT = 9999
NETWORK_HEADER_LENGTH_BYTES = 4
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


class VideoAudioClient:
    """
    Manages connection to streaming server and handles
    video/audio playback synchronization with ENCRYPTION
    """

    def __init__(self, host=DEFAULT_CLIENT_HOST, port=DEFAULT_CLIENT_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.encrypted_conn = None  # (socket, encryption_key)
        self.stream_info = None
        self.is_playing = False
        self.stop_flag = threading.Event()
        self.audio_stream = None
        self.pyaudio_instance = None

    def _connect_to_server(self):
        """Creates the TCP socket and attempts to connect to the server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        print(f"Connected to server {self.host}: {self.port}")

        # ðŸ”’ ENCRYPTION: Perform Diffie-Hellman key exchange
        print("Performing key exchange...")
        temp_conn = (self.socket, None)
        encryption_key = key_exchange.KeyExchange.send_recv_key(temp_conn)
        self.encrypted_conn = (self.socket, encryption_key)
        print(
            f"Encryption established (key length: {len(encryption_key)} bytes)"
        )
        return True

    def _receive_stream_info(self):
        """Receives the initial handshake packet containing
         stream metadata - ENCRYPTED."""
        info_size_data = self.recv_all(NETWORK_HEADER_LENGTH_BYTES)
        if not info_size_data:
            raise ConnectionError("Failed to receive stream info size")

        info_size = struct.unpack("!L", info_size_data)[FIRST_TUPLE_INDEX]
        info_data = self.recv_all(info_size)
        if not info_data:
            raise ConnectionError("Failed to receive stream info data")

        # Decrypt the stream info
        encryption_key = self.encrypted_conn[KEY_INDEX]
        if encryption_key:
            decrypted_data = aes_cipher.AESCipher.decrypt(
                encryption_key,
                info_data
            )
            self.stream_info = pickle.loads(decrypted_data)
        else:
            self.stream_info = pickle.loads(info_data)

        print(f"Stream Info received (ENCRYPTED): ")
        print(
            f"   Video: {self.stream_info['width']}x"
            f"{self.stream_info['height']}"
        )
        print(f"   FPS: {self.stream_info['fps']: .2f}")
        print(f"   Frames: {self.stream_info['total_frames']}")
        print(f"   Has Audio: {self.stream_info['has_audio']}")
        return True

    def _initialize_audio(self):
        """Initializes PyAudio playback if the stream includes audio."""
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
        """Orchestrates the connection process: connect,
         receive info, init audio."""
        try:
            self._connect_to_server()
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
        """Receive an exact number of bytes from the socket"""
        data = b''
        while len(data) < size:
            packet = self.socket.recv(size - len(data))
            if not packet:
                return None
            data += packet
        return data

    def receive_packet(self):
        """Receive one full ENCRYPTED packet (video frame + audio chunk)"""
        try:
            packet_size_data = self.recv_all(NETWORK_HEADER_LENGTH_BYTES)
            if not packet_size_data:
                return None

            packet_size = (
                struct.unpack("!L", packet_size_data)
                [FIRST_TUPLE_INDEX]
            )
            packet_data = self.recv_all(packet_size)

            if not packet_data:
                return None

            # ðŸ”’ Decrypt the packet
            encryption_key = self.encrypted_conn[KEY_INDEX]
            if encryption_key:
                decrypted_data = aes_cipher.AESCipher.decrypt(
                    encryption_key,
                    packet_data
                )
                packet = pickle.loads(decrypted_data)
            else:
                packet = pickle.loads(packet_data)

            return packet

        except Exception as e:
            print(f"Error receiving packet: {e}")
            return None

    def play_stream(self):
        """Manages the video and audio stream playback loop."""
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
        """Initializes and configures the OpenCV display window."""
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name,
                         self.stream_info['width'],
                         self.stream_info['height'])
        cv2.moveWindow(window_name, WINDOW_POSITION_X, WINDOW_POSITION_Y)

    def _process_packet(self, window_name, packet, frame_count):
        """Displays the video frame and plays the audio chunk from a packet."""
        frame = packet['frame']
        cv2.imshow(window_name, frame)
        frame_count += FRAME_INCREMENT_STEP

        if self.audio_stream and packet['audio'] is not None:
            self._play_audio_chunk(packet['audio'])

        return frame_count

    def _play_audio_chunk(self, audio_chunk):
        """Converts the audio chunk to bytes and
         writes it to the audio stream."""
        try:
            audio_bytes = audio_chunk.tobytes()
            self.audio_stream.write(audio_bytes)
        except Exception as e:
            print(f"Audio playback error: {e}")

    @staticmethod
    def _check_user_input(window_name):
        """Checks for user input (Q/ESC) or manual window closing."""
        key = cv2.waitKey(KEYBOARD_WAIT_TIME_MS) & KEY_CODE_MASK_8BIT

        if key == ord('q') or key == ESCAPE_KEY_CODE:
            print("Stopped by user")
            return True

        if (cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) <
                WINDOW_NOT_VISIBLE_THRESHOLD):
            print("Window closed")
            return True

        return False

    @staticmethod
    def _teardown_window():
        """Cleans up OpenCV resources."""
        cv2.destroyAllWindows()

    def cleanup(self):
        """Release resources and close connections"""
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
        if self.socket:
            self.socket.close()
            print("Disconnected from server")
