"""
Gal Haham
Story streaming server for images and videos - ENCRYPTED VERSION
Sends stories with synchronized audio to connected clients over TCP
ENHANCED: Added full encryption support via Diffie-Hellman + AES
"""
import socket
import os
import cv2
import time
import pickle
import struct
import subprocess
import numpy as np
import key_exchange
import aes_cipher

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
SOCK_INDEX = 0
KEY_INDEX = 1


class StoryPlayerServer:

    def __init__(
            self,
            story_filename,
            host=STORY_SERVER_HOST,
            port=STORY_SERVER_PORT
    ):
        self.story_filename = story_filename
        self.host = host
        self.port = port
        self.story_path = os.path.join(STORY_FOLDER, story_filename)
        self.server_socket = None
        self.client_socket = None
        self.encrypted_conn = None

    def extract_audio_info(self, video_path):
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
        try:
            img = self._load_and_resize_image(image_path)
            if img is None:
                return False

            story_info = self._create_image_story_info()

            self._send_story_info_encrypted(story_info)

            success = self._send_image_frames_encrypted(img, story_info['total_frames'])

            if success:
                print("Encrypted image story sent successfully")
            return success

        except (ConnectionResetError, BrokenPipeError, OSError):
            print("Client disconnected")
            return False

    def _load_and_resize_image(self, image_path):
        print("Reading image:", image_path)
        img = cv2.imread(image_path)
        if img is None:
            print("Error: Could not read image")
            return None

        img = cv2.resize(img, (TARGET_FRAME_WIDTH, TARGET_FRAME_HEIGHT))
        return img

    def _create_image_story_info(self):
        return {
            'type': 'IMAGE',
            'width': TARGET_FRAME_WIDTH,
            'height': TARGET_FRAME_HEIGHT,
            'fps': DEFAULT_FPS,
            'total_frames': STORY_TOTAL_FRAME_COUNT,
            'has_audio': False
        }

    def _send_story_info_encrypted(self, story_info):
        try:
            info_data = pickle.dumps(story_info)

            encryption_key = self.encrypted_conn[KEY_INDEX]
            if encryption_key:
                encrypted_data = aes_cipher.AESCipher.encrypt(
                    encryption_key,
                    info_data
                )
            else:
                encrypted_data = info_data

            self.client_socket.sendall(struct.pack("!L", len(encrypted_data)))
            self.client_socket.sendall(encrypted_data)
            print("Encrypted story info sent:", story_info)
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass

    def _send_image_frames_encrypted(self, img, total_frames):
        print("Sending", total_frames, "encrypted frames...")

        for i in range(total_frames):
            frame_packet = self._create_image_frame_packet(img, i)

            if not self._send_packet_encrypted(frame_packet):
                return False

            if i % FRAME_RATE_FPS == ZERO_REMAINDER:
                print("Sent frame", i, "/", total_frames)

            time.sleep(SECONDS_PER_FRAME_CALC / LOG_REPORTING_INTERVAL)

        return True

    def _create_image_frame_packet(self, img, frame_number):
        _, buffer = cv2.imencode(
            '.jpg',
            img,
            [cv2.IMWRITE_JPEG_QUALITY, DESIRED_JPEG_QUALITY]
        )

        frame_data = buffer.tobytes()

        return {
            'frame': cv2.imdecode(
                np.frombuffer(frame_data, np.uint8),
                cv2.IMREAD_COLOR
            ),
            'audio': None,
            'frame_number': frame_number
        }

    def _send_packet_encrypted(self, packet):
        try:
            packet_data = pickle.dumps(packet)

            encryption_key = self.encrypted_conn[KEY_INDEX]
            if encryption_key:
                encrypted_data = aes_cipher.AESCipher.encrypt(
                    encryption_key,
                    packet_data
                )
            else:
                encrypted_data = packet_data

            self.client_socket.sendall(struct.pack("!L", len(encrypted_data)))
            self.client_socket.sendall(encrypted_data)
            return True
        except (ConnectionResetError, BrokenPipeError, OSError):
            return False

    def send_video_story(self, video_path):
        try:
            cap = self._open_video_capture(video_path)
            if not cap:
                return False

            video_props = self._extract_video_properties(cap)

            audio_info = self.extract_audio_info(video_path)

            audio_setup = self._setup_audio_extraction(
                video_path,
                video_props,
                audio_info
            )

            story_info = self._create_video_story_info(
                video_props,
                audio_info,
                audio_setup
            )
            self._send_story_info_encrypted(story_info)

            success = self._stream_video_frames_encrypted(
                cap,
                video_props,
                audio_setup
            )

            self._cleanup_video_resources(
                cap,
                audio_setup.get('audio_process')
            )
            if success:
                print("Encrypted video story sent successfully")
            return success

        except (ConnectionResetError, BrokenPipeError, OSError):
            print("Client disconnected")
            return False

    def _open_video_capture(self, video_path):
        print("Opening video:", video_path)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Could not open video")
            return None
        return cap

    def _extract_video_properties(self, cap):
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= MINIMUM_FPS_LIMIT or fps > MAXIMUM_FPS_LIMIT:
            fps = DEFAULT_FPS

        return {
            'fps': fps,
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'frame_delay': SECONDS_IN_ONE_UNIT / fps
        }

    def _setup_audio_extraction(self, video_path, video_props, audio_info):
        samples_per_frame = int(audio_info['sample_rate'] / video_props['fps'])
        audio_chunk_size = (
            samples_per_frame *
            audio_info['channels'] *
            BYTES_PER_SAMPLE_16_BIT
        )

        audio_process = self._start_ffmpeg_audio_process(
            video_path,
            audio_info
        )

        return {
            'samples_per_frame': samples_per_frame,
            'audio_chunk_size': audio_chunk_size,
            'audio_process': audio_process
        }

    def _start_ffmpeg_audio_process(self, video_path, audio_info):
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
            return audio_process
        except:
            return None

    def _create_video_story_info(self, video_props, audio_info, audio_setup):
        return {
            'type': 'VIDEO',
            'width': video_props['width'],
            'height': video_props['height'],
            'fps': video_props['fps'],
            'total_frames': video_props['total_frames'],
            'has_audio': audio_setup['audio_process'] is not None,
            'audio_sample_rate': audio_info['sample_rate'],
            'audio_channels': audio_info['channels'],
            'samples_per_frame': audio_setup['samples_per_frame']
        }

    def _stream_video_frames_encrypted(self, cap, video_props, audio_setup):
        frame_count = INITIAL_COUNT
        start_time = time.time()

        while True:
            try:
                frame_start = time.time()

                ret, frame = cap.read()
                if not ret:
                    break

                frame = cv2.resize(
                    frame,
                    (TARGET_FRAME_WIDTH, TARGET_FRAME_HEIGHT)
                )

                audio_chunk = self._read_audio_chunk(audio_setup)

                packet = {
                    'frame': frame,
                    'audio': audio_chunk,
                    'frame_number': frame_count
                }

                if not self._send_packet_encrypted(packet):
                    return False

                frame_count += INCREMENT_STEP

                if frame_count % TARGET_FPS == ZERO_REMAINDER:
                    elapsed = time.time() - start_time
                    print("Encrypted Frame", frame_count, "/",
                          video_props['total_frames'], "({:.1f}s)".format(elapsed))

                self._control_frame_rate(frame_start, video_props['frame_delay'])
            except (ConnectionResetError, BrokenPipeError, OSError):
                return False

        return True

    def _read_audio_chunk(self, audio_setup):
        audio_process = audio_setup.get('audio_process')
        audio_chunk_size = audio_setup.get('audio_chunk_size')

        if audio_process and audio_process.stdout:
            try:
                audio_data = audio_process.stdout.read(audio_chunk_size)
                if audio_data and len(audio_data) == audio_chunk_size:
                    return np.frombuffer(audio_data, dtype=np.int16)
            except:
                pass
        return None

    def _control_frame_rate(self, frame_start, frame_delay):
        elapsed = time.time() - frame_start
        sleep_time = max(MINIMUM_DELAY_SECONDS, frame_delay - elapsed)
        if sleep_time > MINIMUM_DELAY_SECONDS:
            time.sleep(sleep_time)

    def _cleanup_video_resources(self, cap, audio_process):
        try:
            cap.release()
        except:
            pass

        if audio_process:
            try:
                audio_process.terminate()
                audio_process.wait()
            except:
                pass

    def validate_story_file(self):
        if not os.path.exists(self.story_path):
            print("Error: Story file not found")
            return False, False, False, None

        ext = os.path.splitext(self.story_filename)[
            FILE_EXTENSION_INDEX
        ].lower()
        is_image = ext in ['.jpg', '.jpeg', '.png', '.bmp']
        is_video = ext in ['.mp4', '.avi', '.mov', '.mkv']

        if not is_image and not is_video:
            print("Error: Unsupported file format:", ext)
            return False, False, False, ext

        return True, is_image, is_video, ext

    def create_server_socket(self):
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
            print("Encrypted Story Server listening on", self.host, ":", self.port)
            return True
        except:
            return False

    def accept_client(self):
        try:
            print("Waiting for client...")
            self.server_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
            self.client_socket, addr = self.server_socket.accept()
            print("Client connected from", addr)

            print("Performing key exchange with", addr, "...")
            temp_conn = (self.client_socket, None)
            encryption_key = key_exchange.KeyExchange.recv_send_key(temp_conn)
            self.encrypted_conn = (self.client_socket, encryption_key)
            print("Encryption established (key length:", len(encryption_key), "bytes)")
            self.client_socket.settimeout(None)
            return True
        except:
            return False

    def cleanup(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

    def start(self):
        print("Starting ENCRYPTED story server")
        print("Story:", self.story_filename)

        is_valid, is_image, is_video, ext = self.validate_story_file()
        if not is_valid:
            return False

        print("Type:", "IMAGE" if is_image else "VIDEO")

        try:
            if not self.create_server_socket():
                return False

            if not self.accept_client():
                return False

            if is_image:
                success = self.send_image_story(self.story_path)
            else:
                success = self.send_video_story(self.story_path)

            if success:
                print("Encrypted story transmission completed")
            else:
                print("Story transmission failed")

            return success

        except:
            pass

        finally:
            self.cleanup()
            print("Story server closed")


def run_story_player_server(story_filename):
    server = StoryPlayerServer(story_filename)
    server.start()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > SCRIPT_NAME_COUNT:
        run_story_player_server(sys.argv[FIRST_ARGUMENT_INDEX])
    else:
        print("Usage: python story_player_server.py <story_filename>")
