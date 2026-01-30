"""
Gal Haham
Client for receiving and playing stories from remote server - ENCRYPTED VERSION
Handles video frames with synchronized audio playback using OpenCV and PyAudio
ENHANCED: Added full encryption support via Diffie-Hellman + AES
"""
import socket
import cv2
import pickle
import struct
import pyaudio
import numpy as np
import key_exchange
import aes_cipher


STORY_SERVER_HOST = "127.0.0.1"
STORY_SERVER_PORT = 6001

FRAME_INCREMENT = 1
MODULO_SUCCESS = 0
FPS_RATE = 30
MESSAGE_LENGTH_FIELD_SIZE = 4
FIRST_UNPACKED_INDEX = 0
STARTING_COUNT = 0
DISPLAY_INDEX_OFFSET = 1
FRAME_DELAY_MS = 1
KEY_ESCAPE = 27
IS_WINDOW_VISIBLE = 1
SOCK_INDEX = 0
KEY_INDEX = 1

# Positions
TEXT_INFO_X = 10
TEXT_INFO_Y = 30
TEXT_AUDIO_STATUS_X = 10
TEXT_AUDIO_STATUS_Y = 60
TEXT_INSTRUCTIONS_X = 10
TEXT_INSTRUCTIONS_Y_OFFSET = 20

# Font Sizes
FONT_SIZE_INFO = 0.7
FONT_SIZE_AUDIO = 0.6
FONT_SIZE_INSTRUCTIONS = 0.6

# Line Thickness
LINE_THICKNESS = 2

# Colors (BGR format for OpenCV)
COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)


class StoryPlayer:
    """
    StoryPlayer is responsible for receiving and playing a recorded story
    from a remote server with FULL ENCRYPTION.

    Responsibilities:
    - Connect to the story server over TCP with encryption
    - Receive ENCRYPTED story metadata (resolution, FPS, audio, total frames)
    - Initialize video and audio playback pipelines
    - Receive and DECRYPT story packets (video frame + optional audio chunk)
    - Display frames using OpenCV and play synchronized audio with PyAudio
    - Support skipping, disconnecting, and cleanup of resources
    """

    def __init__(self, host=STORY_SERVER_HOST, port=STORY_SERVER_PORT):
        """
        Initialize the story player.

        Args:
            host: Server hostname/IP address
            port: Server port number
        """
        self.host = host
        self.port = port
        self.socket = None
        self.encrypted_conn = None  # (socket, encryption_key)
        self.story_info = None
        self.audio_stream = None
        self.pyaudio_instance = None

    def connect(self):
        """
        Connect to server, establish encryption, and receive story metadata.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            print(f"Connecting to server {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to server")

            # ðŸ”’ ENCRYPTION: Perform Diffie-Hellman key exchange
            print("ðŸ” Performing key exchange...")
            temp_conn = (self.socket, None)
            encryption_key = key_exchange.KeyExchange.send_recv_key(temp_conn)
            self.encrypted_conn = (self.socket, encryption_key)
            print(f"âœ… Encryption established (key length: {len(encryption_key)} bytes)")

            # Receive encrypted story info
            if not self._receive_story_info():
                return False

            # Initialize audio if available
            if self.story_info['has_audio']:
                self._initialize_audio()

            return True

        except Exception as e:
            print(f"Connection error: {e}")
            import traceback
            traceback.print_exc()
            if self.socket:
                self.socket.close()
            return False

    def _receive_story_info(self):
        """
        Receive and parse ENCRYPTED story metadata from server.

        Returns:
            bool: True if successful, False otherwise
        """
        # Receive info size
        info_size_data = self._recv_all(MESSAGE_LENGTH_FIELD_SIZE)
        if not info_size_data:
            raise ConnectionError("Failed to receive story info size")

        info_size = (
            struct.unpack("!L", info_size_data)[FIRST_UNPACKED_INDEX]
        )

        # Receive encrypted info data
        encrypted_info_data = self._recv_all(info_size)
        if not encrypted_info_data:
            raise ConnectionError("Failed to receive story info data")

        # ðŸ”’ Decrypt the story info
        encryption_key = self.encrypted_conn[KEY_INDEX]
        try:
            decrypted_data = aes_cipher.AESCipher.decrypt(
                encryption_key,
                encrypted_info_data
            )
            self.story_info = pickle.loads(decrypted_data)
        except Exception as e:
            print(f"âŒ Failed to decrypt story info: {e}")
            return False

        self._print_story_info()

        return True

    def _print_story_info(self):
        """Print received story information to console."""
        print(f"ðŸ”’ Encrypted Story info received: ")
        print(f"   Type: {self.story_info['type']}")
        print(
            f"   Video: {self.story_info['width']}x"
            f"{self.story_info['height']}"
        )
        print(f"   FPS: {self.story_info['fps']:.2f}")
        print(f"   Total frames: {self.story_info['total_frames']}")
        print(f"   Has Audio: {self.story_info['has_audio']}")

    def _initialize_audio(self):
        """
        Initialize PyAudio stream for playback.

        Sets up audio output stream with parameters from story metadata.
        If initialization fails, disables audio for this story.
        """
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.story_info['audio_channels'],
                rate=self.story_info['audio_sample_rate'],
                output=True,
                frames_per_buffer=self.story_info['samples_per_frame']
            )
            print(f"Audio initialized and ready!")
            print(f"   Sample rate: {self.story_info['audio_sample_rate']} Hz")
            print(f"   Channels: {self.story_info['audio_channels']}")
        except Exception as e:
            print(f"Audio initialization failed: {e}")
            self.story_info['has_audio'] = False

    def _recv_all(self, size):
        """
        Receive exact number of bytes from socket.

        Args:
            size: Number of bytes to receive

        Returns:
            bytes: Received data, or None if connection closed
        """
        data = b''
        while len(data) < size:
            packet = self.socket.recv(size - len(data))
            if not packet:
                return None
            data += packet
        return data

    def _receive_packet(self):
        """
        Receive one ENCRYPTED packet (frame + audio) from server.

        Returns:
            dict: Packet containing 'frame' and 'audio', or None if error
        """
        try:
            # Get packet size
            packet_size_data = self._recv_all(MESSAGE_LENGTH_FIELD_SIZE)
            if not packet_size_data:
                return None

            packet_size = (
                struct.unpack("!L", packet_size_data)[FIRST_UNPACKED_INDEX]
            )

            # Get encrypted packet data
            encrypted_packet_data = self._recv_all(packet_size)
            if not encrypted_packet_data:
                return None

            # ðŸ”’ Decrypt the packet
            encryption_key = self.encrypted_conn[KEY_INDEX]
            try:
                decrypted_data = aes_cipher.AESCipher.decrypt(
                    encryption_key,
                    encrypted_packet_data
                )
                packet = pickle.loads(decrypted_data)
                return packet
            except Exception as e:
                print(f"âŒ Failed to decrypt packet: {e}")
                return None

        except Exception as e:
            print(f"Error receiving packet: {e}")
            return None

    def play_story(self):
        """
        Main playback loop - displays video and plays audio.
        All data is ENCRYPTED during transmission.
        """
        if not self.story_info:
            print("No story info available")
            return

        # Setup window
        window_name = self._setup_playback_window()

        # Main playback loop
        frame_count = STARTING_COUNT
        print(f"ðŸ”’ Playing ENCRYPTED {self.story_info['type']} story...")

        while True:
            # Receive encrypted packet
            packet = self._receive_packet()
            if packet is None:
                print("Story ended")
                break

            # Process and display frame
            frame = packet['frame']
            self._add_overlay_text(frame, frame_count)
            cv2.imshow(window_name, frame)

            # Play audio
            self._play_audio_chunk(packet)

            # Update counter and print progress
            frame_count += FRAME_INCREMENT
            self._print_progress(frame_count)

            # Check for user input or window close
            if self._check_exit_conditions(window_name):
                break

        # Cleanup
        cv2.destroyAllWindows()
        self.cleanup()
        print(f"Playback finished ({frame_count} frames)")

    def _setup_playback_window(self):
        """
        Setup OpenCV window for story playback.

        Returns:
            str: Window name
        """
        window_name = f"ðŸ”’ Encrypted Story - {self.story_info['type']}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(
            window_name,
            self.story_info['width'],
            self.story_info['height']
        )
        return window_name

    def _add_overlay_text(self, frame, frame_count):
        """
        Add overlay text to frame (info, audio status, instructions).

        Args:
            frame: OpenCV frame to add text to
            frame_count: Current frame number
        """
        # Frame info with encryption indicator
        self._add_frame_info_text(frame, frame_count)

        # Audio status
        self._add_audio_status_text(frame)

        # Instructions
        self._add_instructions_text(frame)

    def _add_frame_info_text(self, frame, frame_count):
        """
        Add frame counter and type info to top of frame.

        Args:
            frame: OpenCV frame
            frame_count: Current frame number
        """
        info_text = (
            f"ðŸ”’ {self.story_info['type']} | "
            f"Frame: {frame_count + DISPLAY_INDEX_OFFSET}/"
            f"{self.story_info['total_frames']}"
        )

        cv2.putText(
            frame,
            info_text,
            (TEXT_INFO_X, TEXT_INFO_Y),
            cv2.FONT_HERSHEY_SIMPLEX,
            FONT_SIZE_INFO,
            COLOR_WHITE,
            LINE_THICKNESS
        )

    def _add_audio_status_text(self, frame):
        """
        Add audio status indicator to frame.

        Args:
            frame: OpenCV frame
        """
        # Determine status and color
        has_audio = self.story_info['has_audio'] and self.audio_stream
        audio_status = "Audio: ON" if has_audio else "Audio: OFF"
        color = COLOR_GREEN if has_audio else COLOR_RED

        cv2.putText(
            frame,
            audio_status,
            (TEXT_AUDIO_STATUS_X, TEXT_AUDIO_STATUS_Y),
            cv2.FONT_HERSHEY_SIMPLEX,
            FONT_SIZE_AUDIO,
            color,
            LINE_THICKNESS
        )

    def _add_instructions_text(self, frame):
        """
        Add user instructions to bottom of frame.

        Args:
            frame: OpenCV frame
        """
        y_position = self.story_info['height'] - TEXT_INSTRUCTIONS_Y_OFFSET

        cv2.putText(
            frame,
            "Press 'Q' or ESC to skip",
            (TEXT_INSTRUCTIONS_X, y_position),
            cv2.FONT_HERSHEY_SIMPLEX,
            FONT_SIZE_INSTRUCTIONS,
            COLOR_YELLOW,
            LINE_THICKNESS
        )

    def _play_audio_chunk(self, packet):
        """
        Play audio chunk from packet if available.

        Args:
            packet: Packet dictionary containing 'audio' field
        """
        if self.audio_stream and packet['audio'] is not None:
            try:
                audio_bytes = packet['audio'].tobytes()
                self.audio_stream.write(audio_bytes)
            except Exception as e:
                print(f"Audio playback error: {e}")

    def _print_progress(self, frame_count):
        """
        Print playback progress periodically.

        Args:
            frame_count: Current frame number
        """
        if frame_count % FPS_RATE == MODULO_SUCCESS:
            print(
                f"ðŸ”’ Playing encrypted frame {frame_count}/"
                f"{self.story_info['total_frames']}"
            )

    def _check_exit_conditions(self, window_name):
        """
        Check if user wants to exit or window was closed.

        Args:
            window_name: Name of OpenCV window

        Returns:
            bool: True if should exit, False otherwise
        """
        # Check for key press
        key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
        if key == KEY_ESCAPE or key == ord('q') or key == ord('Q'):
            print("Story skipped by user")
            return True

        # Check if window closed
        if cv2.getWindowProperty(window_name,
                                 cv2.WND_PROP_VISIBLE) < IS_WINDOW_VISIBLE:
            print("Window closed")
            return True

        return False

    def cleanup(self):
        """
        Release resources such as audio stream, PyAudio and socket.

        Called automatically at end of playback or on error.
        """
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
        if self.socket:
            self.socket.close()
            print("Disconnected from server")


def run_story_player_client():
    """
    Entry point for running the ENCRYPTED story player client.

    Creates a StoryPlayer instance, connects to server, and starts playback.
    """
    player = StoryPlayer()
    if player.connect():
        player.play_story()
    else:
        print("Failed to connect to server")


if __name__ == '__main__':
    run_story_player_client()