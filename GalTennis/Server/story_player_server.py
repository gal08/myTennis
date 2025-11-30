"""
Gal Haham
Story streaming server for images and videos.
Sends stories with synchronized audio to connected clients over TCP.
"""
import socket
import os
import cv2
import time
import pickle
import struct
import subprocess
import numpy as np

STORY_SERVER_HOST = '0.0.0.0'
STORY_SERVER_PORT = 6001
STORY_FOLDER = "stories"
MAX_SPLIT_COUNT = 1
DEFAULT_AUDIO_SAMPLE_RATE = 44100
DEFAULT_AUDIO_CHANNELS = 2
DESIRED_JPEG_QUALITY = 80
FRAME_RATE_FPS = 30
LOG_REPORTING_INTERVAL = 30
SECONDS_PER_FRAME_CALC = 1
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
LARGE_IO_BUFFER_SIZE_BYTES = 100000000
INCREMENT_STEP = 1
TARGET_FPS = 30
MINIMUM_DELAY_SECONDS = 0
SOCKET_OPTION_ENABLED = 1
SINGLE_CONNECTION_BACKLOG = 1
SOCKET_TIMEOUT_SECONDS = 30
SCRIPT_NAME_COUNT = 1
FIRST_ARGUMENT_INDEX = 1
FILE_EXTENSION_INDEX = 1


class StoryPlayerServer:
    """
    Story streaming server that handles both image and video stories.
    Manages client connections and streams media with synchronized audio.
    """

    def __init__(
            self,
            story_filename,
            host=STORY_SERVER_HOST,
            port=STORY_SERVER_PORT
    ):
        """
        Initialize the story player server.

        Args:
            story_filename: Name of the story file to stream
            host: Server host address
            port: Server port number
        """
        self.story_filename = story_filename
        self.host = host
        self.port = port
        self.story_path = os.path.join(STORY_FOLDER, story_filename)
        self.server_socket = None
        self.client_socket = None

    def extract_audio_info(self, video_path):
        """
        Extract audio information from video using ffprobe.

        Args:
            video_path: Path to the video file

        Returns:
            dict: Audio information with sample_rate and channels
        """
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=sample_rate,channels',
                '-of', 'default=noprint_wrappers=1',
                video_path
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            info = {}
            for line in result.stdout.splitlines():
                if '=' in line:
                    k, v = line.strip().split('=', MAX_SPLIT_COUNT)
                    info[k] = v

            return {
                'sample_rate': int(
                    info.get('sample_rate', DEFAULT_AUDIO_SAMPLE_RATE)
                ),
                'channels': int(
                    info.get('channels', DEFAULT_AUDIO_CHANNELS)
                )
            }
        except:
            return {
                'sample_rate': DEFAULT_AUDIO_SAMPLE_RATE,
                'channels': DEFAULT_AUDIO_CHANNELS
            }

    def send_image_story(self, image_path):
        """
        Send a static image as a story (displayed for 5 seconds).

        Args:
            image_path: Path to the image file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f" Reading image: {image_path}")
            img = cv2.imread(image_path)
            if img is None:
                print(f" Error: Could not read image")
                return False

            img = cv2.resize(img, (TARGET_FRAME_WIDTH, TARGET_FRAME_HEIGHT))

            # Send story info
            story_info = {
                'type': 'IMAGE',
                'width': TARGET_FRAME_WIDTH,
                'height': TARGET_FRAME_HEIGHT,
                'fps': DEFAULT_FPS,
                'total_frames': STORY_TOTAL_FRAME_COUNT,
                'has_audio': False
            }

            info_data = pickle.dumps(story_info)
            self.client_socket.sendall(struct.pack("!L", len(info_data)))
            self.client_socket.sendall(info_data)
            print(f"✓ Story info sent: {story_info}")

            # Send frames
            print(f"Sending {story_info['total_frames']} frames...")
            for i in range(story_info['total_frames']):
                _, buffer = cv2.imencode(
                    '.jpg',
                    img,
                    [cv2.IMWRITE_JPEG_QUALITY, DESIRED_JPEG_QUALITY]
                )

                frame_data = buffer.tobytes()

                packet = {
                    'frame': cv2.imdecode(
                        np.frombuffer(frame_data, np.uint8),
                        cv2.IMREAD_COLOR
                    ),
                    'audio': None,
                    'frame_number': i
                }

                packet_data = pickle.dumps(packet)
                self.client_socket.sendall(struct.pack("!L", len(packet_data)))
                self.client_socket.sendall(packet_data)

                if i % FRAME_RATE_FPS == ZERO_REMAINDER:
                    print(f"Sent frame {i}/{story_info['total_frames']}")

                time.sleep(SECONDS_PER_FRAME_CALC / LOG_REPORTING_INTERVAL)

            print(f"✓ Image story sent successfully")
            return True

        except Exception as e:
            print(f"Error sending image: {e}")
            import traceback
            traceback.print_exc()
            return False

    def send_video_story(self, video_path):
        """
        Send a video story with synchronized audio.

        Args:
            video_path: Path to the video file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Opening video: {video_path}")
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Error: Could not open video")
                return False

            # Get video info
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= MINIMUM_FPS_LIMIT or fps > MAXIMUM_FPS_LIMIT:
                fps = DEFAULT_FPS

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_delay = SECONDS_IN_ONE_UNIT / fps

            # Get audio info
            audio_info = self.extract_audio_info(video_path)
            print(f"Audio info: {audio_info}")

            # Calculate audio chunk size
            samples_per_frame = int(audio_info['sample_rate'] / fps)
            audio_chunk_size = (
                samples_per_frame *
                audio_info['channels'] *
                BYTES_PER_SAMPLE_16_BIT
            )

            # Start ffmpeg for audio extraction
            audio_process = None
            try:
                ffmpeg_cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vn',
                    '-acodec', 'pcm_s16le',
                    '-ar', str(audio_info['sample_rate']),
                    '-ac', str(audio_info['channels']),
                    '-f', 's16le',
                    'pipe:1'
                ]
                audio_process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    bufsize=LARGE_IO_BUFFER_SIZE_BYTES
                )
                print("✓ FFmpeg audio process started")
            except Exception as e:
                print(f" Warning: Could not start audio extraction: {e}")

            # Send story info
            story_info = {
                'type': 'VIDEO',
                'width': width,
                'height': height,
                'fps': fps,
                'total_frames': total_frames,
                'has_audio': audio_process is not None,
                'audio_sample_rate': audio_info['sample_rate'],
                'audio_channels': audio_info['channels'],
                'samples_per_frame': samples_per_frame
            }

            info_data = pickle.dumps(story_info)
            self.client_socket.sendall(struct.pack("!L", len(info_data)))
            self.client_socket.sendall(info_data)
            print(f"✓ Story info sent")
            print(f"   Video: {width}x{height} @ {fps:.2f} FPS")
            print(
                f"   Audio: {audio_info['sample_rate']} Hz, "
                f"{audio_info['channels']} ch"
            )
            print(f"   Has Audio: {story_info['has_audio']}")

            # Send frames with audio
            frame_count = INITIAL_COUNT
            start_time = time.time()

            while True:
                frame_start = time.time()
                ret, frame = cap.read()
                if not ret:
                    print(f"End of video at frame {frame_count}")
                    break

                # Resize frame
                frame = cv2.resize(
                    frame,
                    (TARGET_FRAME_WIDTH, TARGET_FRAME_HEIGHT)
                )

                # Get audio chunk
                audio_chunk = None
                if audio_process and audio_process.stdout:
                    try:
                        audio_data = (
                            audio_process.stdout.read(audio_chunk_size)
                        )
                        if audio_data and len(audio_data) == audio_chunk_size:
                            audio_chunk = np.frombuffer(
                                audio_data,
                                dtype=np.int16
                            )
                    except:
                        audio_chunk = None

                # Create and send packet
                packet = {
                    'frame': frame,
                    'audio': audio_chunk,
                    'frame_number': frame_count
                }

                packet_data = pickle.dumps(packet)
                self.client_socket.sendall(struct.pack("!L", len(packet_data)))
                self.client_socket.sendall(packet_data)

                frame_count += INCREMENT_STEP

                if frame_count % TARGET_FPS == ZERO_REMAINDER:
                    elapsed = time.time() - start_time
                    print(
                        f"Frame {frame_count}/{total_frames} "
                        f"({elapsed:.1f}s)"
                    )

                # Frame rate control
                elapsed = time.time() - frame_start
                sleep_time = max(MINIMUM_DELAY_SECONDS, frame_delay - elapsed)
                if sleep_time > MINIMUM_DELAY_SECONDS:
                    time.sleep(sleep_time)

            # Cleanup
            cap.release()
            if audio_process:
                audio_process.terminate()
                audio_process.wait()

            print(f"✓ Video story sent successfully ({frame_count} frames)")
            return True

        except Exception as e:
            print(f"Error sending video: {e}")
            import traceback
            traceback.print_exc()
            return False

    def validate_story_file(self):
        """
        Validate that the story file exists and is of supported format.

        Returns:
            tuple: (is_valid, is_image, is_video, extension)
        """
        if not os.path.exists(self.story_path):
            print(f"Error: Story file not found")
            return False, False, False, None

        ext = (
            os.path.splitext(self.story_filename)[FILE_EXTENSION_INDEX]
            .lower()
        )
        is_image = ext in ['.jpg', '.jpeg', '.png', '.bmp']
        is_video = ext in ['.mp4', '.avi', '.mov', '.mkv']

        if not is_image and not is_video:
            print(f"Error: Unsupported file format: {ext}")
            return False, False, False, ext

        return True, is_image, is_video, ext

    def create_server_socket(self):
        """
        Create and configure the server socket.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.server_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )
            self.server_socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                SOCKET_OPTION_ENABLED
            )
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(SINGLE_CONNECTION_BACKLOG)
            print(f"✓ Server listening on {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Error creating server socket: {e}")
            return False

    def accept_client(self):
        """
        Accept a client connection with timeout.

        Returns:
            bool: True if client connected, False otherwise
        """
        try:
            print(f"Waiting for client...")
            self.server_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
            self.client_socket, addr = self.server_socket.accept()
            print(f"✓ Client connected from {addr}")
            self.client_socket.settimeout(None)
            return True
        except socket.timeout:
            print("Error: Timeout waiting for client")
            return False
        except Exception as e:
            print(f"Error accepting client: {e}")
            return False

    def cleanup(self):
        """Clean up socket resources."""
        if self.client_socket:
            try:
                self.client_socket.close()
                print("Client socket closed")
            except:
                pass

        if self.server_socket:
            try:
                self.server_socket.close()
                print("Server socket closed")
            except:
                pass

    def start(self):
        """
        Main method to start the story streaming server.

        Returns:
            bool: True if streaming completed successfully, False otherwise
        """
        print(f"Starting story server")
        print(f"Story: {self.story_filename}")
        print(f"Path: {self.story_path}")

        # Validate story file
        is_valid, is_image, is_video, ext = self.validate_story_file()
        if not is_valid:
            return False

        print(f"Type: {'IMAGE' if is_image else 'VIDEO'}")

        try:
            # Create server socket
            if not self.create_server_socket():
                return False

            # Accept client connection
            if not self.accept_client():
                return False

            # Send story
            if is_image:
                success = self.send_image_story(self.story_path)
            else:
                success = self.send_video_story(self.story_path)

            if success:
                print("Story transmission completed successfully")
            else:
                print("Story transmission failed")

            return success

        except Exception as e:
            print(f"Server error: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.cleanup()
            print("Server shutdown complete")


def run_story_player_server(story_filename):
    """
    Convenience function to create and start a story player server.

    Args:
        story_filename: Name of the story file to stream
    """
    server = StoryPlayerServer(story_filename)
    server.start()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > SCRIPT_NAME_COUNT:
        run_story_player_server(sys.argv[FIRST_ARGUMENT_INDEX])
    else:
        print("Usage: python story_player_server.py <story_filename>")
