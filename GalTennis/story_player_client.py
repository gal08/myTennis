import socket
import cv2
import pickle
import struct
import pyaudio
import numpy as np

STORY_SERVER_HOST = '127.0.0.1'
STORY_SERVER_PORT = 6001


class StoryPlayer:
    def __init__(self, host=STORY_SERVER_HOST, port=STORY_SERVER_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.story_info = None
        self.audio_stream = None
        self.pyaudio_instance = None

    def connect(self):
        """Connect to server and receive story info"""
        try:
            print(f"Connecting to server {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"✓ Connected to server")

            # Receive story info
            info_size_data = self._recv_all(4)
            if not info_size_data:
                raise ConnectionError("Failed to receive story info size")

            info_size = struct.unpack("!L", info_size_data)[0]
            info_data = self._recv_all(info_size)
            if not info_data:
                raise ConnectionError("Failed to receive story info data")

            self.story_info = pickle.loads(info_data)
            print(f"✓ Story info received:")
            print(f"   Type: {self.story_info['type']}")
            print(
                f"   Video: {self.story_info['width']}x"
                f"{self.story_info['height']}"
            )
            print(f"   FPS: {self.story_info['fps']:.2f}")
            print(f"   Total frames: {self.story_info['total_frames']}")
            print(f"   Has Audio: {self.story_info['has_audio']}")

            # Initialize audio if available
            if self.story_info['has_audio']:
                self._initialize_audio()

            return True

        except Exception as e:
            print(f"Connection error: {e}")
            if self.socket:
                self.socket.close()
            return False

    def _initialize_audio(self):
        """Initialize PyAudio for playback"""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.story_info['audio_channels'],
                rate=self.story_info['audio_sample_rate'],
                output=True,
                frames_per_buffer=self.story_info['samples_per_frame']
            )
            print(f"✓✓✓ Audio initialized and ready! ✓✓✓")
            print(f"   Sample rate: {self.story_info['audio_sample_rate']} Hz")
            print(f"   Channels: {self.story_info['audio_channels']}")
        except Exception as e:
            print(f"Audio initialization failed: {e}")
            self.story_info['has_audio'] = False

    def _recv_all(self, size):
        """Receive exact number of bytes"""
        data = b''
        while len(data) < size:
            packet = self.socket.recv(size - len(data))
            if not packet:
                return None
            data += packet
        return data

    def _receive_packet(self):
        """Receive one packet (frame + audio)"""
        try:
            # Get packet size
            packet_size_data = self._recv_all(4)
            if not packet_size_data:
                return None

            packet_size = struct.unpack("!L", packet_size_data)[0]
            packet_data = self._recv_all(packet_size)
            if not packet_data:
                return None

            packet = pickle.loads(packet_data)
            return packet

        except Exception as e:
            print(f"Error receiving packet: {e}")
            return None

    def play_story(self):
        """Main playback loop"""
        if not self.story_info:
            print("No story info available")
            return

        window_name = f"Story - {self.story_info['type']}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(
            window_name,
            self.story_info['width'],
            self.story_info['height']
        )

        frame_count = 0
        print(f"Playing {self.story_info['type']} story...")

        while True:
            packet = self._receive_packet()
            if packet is None:
                print("Story ended")
                break

            # Display frame
            frame = packet['frame']

            # Add overlay info
            info_text = (
                f"{self.story_info['type']} | "
                f"Frame: {frame_count + 1}/{self.story_info['total_frames']}"
            )

            cv2.putText(frame, info_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            audio_status = (
                "Audio: ON"
                if self.story_info['has_audio'] and self.audio_stream
                else "Audio: OFF"
            )

            color = (
                (0, 255, 0)
                if self.story_info['has_audio'] and self.audio_stream
                else (0, 0, 255)
            )

            cv2.putText(frame, audio_status, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            cv2.putText(
                frame,
                "Press 'Q' or ESC to skip",
                (10, self.story_info['height'] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

            cv2.imshow(window_name, frame)

            # Play audio if available
            if self.audio_stream and packet['audio'] is not None:
                try:
                    audio_bytes = packet['audio'].tobytes()
                    self.audio_stream.write(audio_bytes)
                except Exception as e:
                    print(f"Audio playback error: {e}")

            frame_count += 1

            if frame_count % 30 == 0:
                print(
                    f"Playing frame {frame_count}/"
                    f"{self.story_info['total_frames']}"
                )

            # Check for user input
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q') or key == ord('Q'):
                print("Story skipped by user")
                break

            # Check if window closed
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("Window closed")
                break

        cv2.destroyAllWindows()
        self.cleanup()
        print(f"Playback finished ({frame_count} frames)")

    def cleanup(self):
        """Clean up resources"""
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
        if self.socket:
            self.socket.close()
            print("Disconnected from server")


def run_story_player_client():
    """Main client entry point"""
    player = StoryPlayer()
    if player.connect():
        player.play_story()
    else:
        print("Failed to connect to server")


if __name__ == '__main__':
    run_story_player_client()
