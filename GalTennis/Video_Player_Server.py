"""
Gal Haham
Video & audio streaming server for sending media to clients in real time.
"""
import socket        # for creating server connections
import cv2           # for reading and processing video
import pickle        # for serializing data before sending
import struct        # for packing/unpacking binary data
import threading     # for handling multiple clients at once
import time          # for measuring delays and sleep
import subprocess    # for running external programs (ffmpeg, ffprobe)
import numpy as np   # for handling numerical data (like audio)

DEFAULT_HOST = '0.0.0.0'  # server will accept connections from any IP
DEFAULT_PORT = 9999  # default TCP port number for streaming
MAX_PENDING_CONNECTIONS = 5  # number of waiting clients allowed
NETWORK_LEN_BYTES = 4   # number of bytes used to send message size
DEFAULT_FPS_FALLBACK = 30.0   # default FPS used if video FPS is invalid
PROGRESS_LOG_EVERY_N_FRAMES = 30  # how often to print streaming progress
AUDIO_DEFAULT_SAMPLE_RATE = 44100          # default sample rate if not found
AUDIO_DEFAULT_CHANNELS = 2  # default number of audio channels (stereo)
BYTES_PER_SAMPLE_16BIT = 2  # each 16-bit audio sample uses 2 bytes
FFMPEG_STDOUT_BUFFER_BYTES = 100000000     # size of ffmpeg buffer (100 MB)
REUSE_ADDRESS_ENABLED = 1  # allows reusing the same address after restart
MAX_SPLITS_FOR_KEY_VALUE = 1  # when splitting key=value text, split only once
INVALID_FPS_THRESHOLD = 0  # minimum allowed FPS value (if <=0, use default)
SECONDS_PER_FRAME_CALCULATION_UNIT = 1.0   # 1 second used to frame delay
INITIAL_FRAME_COUNT = 0                    # start frame counter from 0
FRAME_INCREMENT_STEP = 1      # increase frame count by 1 each loop
FRAME_COUNT_RESET_VALUE = 0   # reset reference for progress logging
MINIMUM_SLEEP_TIME_SECONDS = 0.0           # minimum allowed sleep time


class VideoAudioServer:  # class that manages video & audio streaming
    def __init__(self, video_file, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.video_path = video_file  # path to the video file
        self.host = host  # host IP for the server
        self.port = port  # port number for connections
        self.server_socket = None  # placeholder for the socket

    def _initialize_and_listen(self):
        # Create socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Set socket option to reuse address
        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            REUSE_ADDRESS_ENABLED
        )

        # Bind host and port
        self.server_socket.bind((self.host, self.port))

        # Start listening for connections
        self.server_socket.listen(MAX_PENDING_CONNECTIONS)

    def _log_startup_info(self):
        """Prints initial server and video information to the console."""
        print(f"Server started on {self.host}:{self.port}")
        print(f"Video: {self.video_path}")  # show which video is used
        print("Waiting for clients...")  # wait for client connections

    def _accept_clients_loop(self):
        """Enters the main loop to accept
        new clients and spawn handler threads."""
        while True:  # loop forever to handle multiple clients
            try:
                # accept a new client connection
                client_socket, address = self.server_socket.accept()

                # show connected client address
                print(f"Client connected: {address}")

                # create and start a new thread for this client
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True  # make thread close with main program
                )
                client_thread.start()

            except Exception as e:
                print(f"Error in client acceptance loop: {e}")
                break

    def start(self):
        """Orchestrates the server startup process: init, log, and listen."""
        self._initialize_and_listen()
        self._log_startup_info()
        self._accept_clients_loop()

    def _run_ffprobe(self):
        """Runs ffprobe command to get raw audio stream information."""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=sample_rate,channels,codec_name',
            '-of', 'default=noprint_wrappers=1',
            self.video_path
        ]

        # run command and capture output
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

    @staticmethod
    def _parse_ffprobe_output(result):
        """Parses ffprobe stdout into a key-value dictionary."""
        info = {}
        # loop through each line of output
        for line in result.stdout.splitlines():
            if '=' in line:  # only process lines with '='
                # split into key and value
                k, v = line.strip().split('=', MAX_SPLITS_FOR_KEY_VALUE)
                info[k] = v  # store in dictionary
        return info

    @staticmethod
    def _safe_get_int(info_dict, key, default_value):
        """Safely gets a value from dict and converts
        it to int, or uses default."""
        try:
            # convert value to int
            return int(info_dict.get(key, default_value))
        except ValueError:
            # fallback if conversion fails (e.g., 'N/A' or corrupt data)
            return default_value

    def extract_audio_info(self):
        """Orchestrates audio information extraction from the video."""
        try:
            # 1. Run the external process
            result = self._run_ffprobe()

            # 2. Process the raw output
            info = self._parse_ffprobe_output(result)

            # 3. Safely extract and validate specific values
            sample_rate = self._safe_get_int(
                info, 'sample_rate', AUDIO_DEFAULT_SAMPLE_RATE
            )
            channels = self._safe_get_int(
                info, 'channels', AUDIO_DEFAULT_CHANNELS
            )

            # 4. Return the final structured data
            return {
                'sample_rate': sample_rate,
                'channels': channels,
                'codec': info.get('codec_name', 'unknown'),
            }

        except FileNotFoundError:  # if ffprobe is not installed
            print("Error: ffprobe command not found.")
            print("Audio extraction skipped.")
            # Fallback values
            return {
                'sample_rate': AUDIO_DEFAULT_SAMPLE_RATE,
                'channels': AUDIO_DEFAULT_CHANNELS,
                'codec': 'unknown',
            }

        except subprocess.CalledProcessError as e:  # if ffprobe fails
            print((
                f"Error running ffprobe (Code: {e.returncode}): "
                f"{e.stderr.strip()}"
            ))
            # Fallback values
            return {
                'sample_rate': AUDIO_DEFAULT_SAMPLE_RATE,
                'channels': AUDIO_DEFAULT_CHANNELS,
                'codec': 'unknown',
            }

    def _setup_video(self, address):
        """Opens video file and extracts core video stream information."""
        cap = cv2.VideoCapture(self.video_path)  # open video file
        if not cap.isOpened():  # check if video is valid
            print(f"Cannot open video for client {address}")
            return None, None

        # Get video info
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= INVALID_FPS_THRESHOLD:  # check if fps is invalid
            fps = DEFAULT_FPS_FALLBACK  # use default fps

        # Calculate delay time per frame and get dimensions
        # delay time per frame
        frame_delay = SECONDS_PER_FRAME_CALCULATION_UNIT / fps
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # get video width
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # get video height
        # total number of frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        video_info = {
            'fps': fps,
            'width': width,
            'height': height,
            'total_frames': total_frames,
            'frame_delay': frame_delay
        }
        return cap, video_info

    def _setup_audio_process(self, video_info):
        """Sets up audio info, calculates chunk size,
        and starts the FFmpeg process."""

        audio_info = self.extract_audio_info()
        fps = video_info['fps']

        # Calculate audio chunk size (samples per frame)
        samples_per_frame = int(audio_info['sample_rate'] / fps)
        audio_chunk_size = (
                samples_per_frame *
                audio_info['channels'] *
                BYTES_PER_SAMPLE_16BIT
        )  # bytes per audio chunk

        ffmpeg_cmd = [  # build ffmpeg command
            'ffmpeg',
            '-i', self.video_path,
            '-vn',  # disable video
            '-acodec', 'pcm_s16le',  # 16-bit audio format
            '-ar', str(audio_info['sample_rate']),  # set audio sample rate
            '-ac', str(audio_info['channels']),  # set audio channels
            '-f', 's16le',  # raw audio format
            'pipe:1'  # output to stdout
        ]

        audio_process = None
        try:
            audio_process = subprocess.Popen(  # start ffmpeg process
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=FFMPEG_STDOUT_BUFFER_BYTES
            )
        except FileNotFoundError:  # ffmpeg not found
            print("FFmpeg not available, streaming video only")
        except OSError as e:  # ffmpeg failed to start
            print(f"Failed to start FFmpeg: {e}")

        audio_setup = {
            'audio_process': audio_process,
            'audio_chunk_size': audio_chunk_size,
            'samples_per_frame': samples_per_frame,
            'audio_sample_rate': audio_info['sample_rate'],
            'audio_channels': audio_info['channels'],
        }
        return audio_setup

    @staticmethod
    def _send_stream_info(client_socket, video_info, audio_setup, address):
        """Consolidates video/audio info,
        sends handshake packet, and logs details."""

        stream_info = {
            'fps': video_info['fps'],
            'width': video_info['width'],
            'height': video_info['height'],
            'total_frames': video_info['total_frames'],
            'audio_sample_rate': audio_setup['audio_sample_rate'],
            'audio_channels': audio_setup['audio_channels'],
            'samples_per_frame': audio_setup['samples_per_frame'],
            'has_audio': audio_setup['audio_process'] is not None
        }

        info_data = pickle.dumps(stream_info)  # convert info to bytes
        info_size = struct.pack("!L", len(info_data))  # pack length of info
        client_socket.sendall(info_size + info_data)  # send to client

        print(f"Streaming to {address}")  # print client info
        # show video details
        print((
            f"   Video: {video_info['width']}x{video_info['height']} "
            f"@ {video_info['fps']:.2f} FPS"
        ))
        print(
            f"   Audio: {audio_setup['audio_sample_rate']} Hz, "
            f"{audio_setup['audio_channels']} ch"
        )  # show audio details
        return stream_info

    @staticmethod
    def _get_audio_chunk(audio_process, audio_chunk_size):
        """Reads one audio chunk from the ffmpeg process
         and converts it to numpy array."""
        audio_chunk = None  # default: no audio
        if audio_process and audio_process.stdout:
            try:
                audio_data = audio_process.stdout.read(
                    audio_chunk_size
                )
                if audio_data and len(audio_data) == audio_chunk_size:
                    audio_chunk = np.frombuffer(
                        audio_data,
                        dtype=np.int16
                    )
                else:
                    audio_chunk = None  # Incomplete chunk or end of stream
            except (OSError, ValueError, BufferError, AttributeError):
                audio_chunk = None
        return audio_chunk

    @staticmethod
    def _log_progress(frame_count, total_frames, start_time, address):
        """Logs streaming progress periodically."""
        # Print progress every 30 frames
        if (
                frame_count % PROGRESS_LOG_EVERY_N_FRAMES ==
                FRAME_COUNT_RESET_VALUE
        ):
            elapsed = time.time() - start_time
            print(
                f"Client {address}: Frame {frame_count}/"
                f"{total_frames} ({elapsed:.1f}s)"
            )

    @staticmethod
    def _control_frame_rate(frame_start, frame_delay):
        """Pauses execution to maintain the target frame rate."""
        elapsed = time.time() - frame_start  # time taken for frame
        sleep_time = max(
            MINIMUM_SLEEP_TIME_SECONDS,
            frame_delay - elapsed
        )
        if sleep_time > MINIMUM_SLEEP_TIME_SECONDS:  # sleep if needed
            time.sleep(sleep_time)

    def _main_streaming_loop(
            self,
            client_socket,
            cap,
            audio_process,
            audio_chunk_size,
            frame_delay,
            address,
            total_frames
    ):
        """The main loop for reading video frames,
        audio chunks, and sending packets."""
        frame_count = INITIAL_FRAME_COUNT  # start counting frames
        start_time = time.time()  # mark start time

        while True:  # loop for each video frame
            frame_start = time.time()  # mark frame start time
            ret, frame = cap.read()  # read next video frame
            if not ret:  # stop if no more frames
                print(
                    f"Finished streaming to {address} "
                    f"({frame_count} frames)"
                )
                break

            audio_chunk = self._get_audio_chunk(
                audio_process,
                audio_chunk_size
            )

            # Prepare, serialize, and send packet
            packet = {
                'frame': frame,
                'audio': audio_chunk,
                'frame_number': frame_count
            }
            packet_data = pickle.dumps(packet)  # serialize packet
            packet_size = struct.pack("!L", len(packet_data))
            client_socket.sendall(packet_size + packet_data)  # send packet

            frame_count += FRAME_INCREMENT_STEP  # increase frame counter

            # Logging and frame rate control
            self._log_progress(frame_count, total_frames, start_time, address)
            self._control_frame_rate(frame_start, frame_delay)

        return frame_count

    @staticmethod
    def _cleanup_client_resources(cap, audio_process, client_socket, address):
        """Releases all resources associated
        with a single client connection."""
        if cap:
            cap.release()  # release video file
        if audio_process:
            audio_process.terminate()  # stop ffmpeg
            audio_process.wait()  # wait until it closes
        client_socket.close()  # close client connection
        print(f"Connection closed: {address}")

    def handle_client(self, client_socket, address):
        """Orchestrates the video and audio streaming
        to a connected client (Main entry)."""
        cap = None
        audio_process = None

        try:
            # 1. Setup Video
            cap, video_info = self._setup_video(address)
            if not cap:
                client_socket.close()
                return

            # 2. Setup Audio
            audio_setup = self._setup_audio_process(video_info)
            audio_process = audio_setup['audio_process']

            # 3. Handshake (Send stream info)
            self._send_stream_info(
                client_socket,
                video_info,
                audio_setup,
                address
            )

            # 4. Main Streaming Loop
            self._main_streaming_loop(
                client_socket,
                cap,
                audio_process,
                audio_setup['audio_chunk_size'],
                video_info['frame_delay'],
                address,
                video_info['total_frames']
            )

        except (ConnectionResetError, BrokenPipeError):  # client disconnected
            print(f" Client {address} disconnected")
        except Exception as e:  # other errors
            print(f" Error with client {address}: {e}")
        finally:
            self._cleanup_client_resources(
                cap,
                audio_process,
                client_socket,
                address
            )


def run_video_player_server(video_path):
    server = VideoAudioServer(video_path, host=DEFAULT_HOST, port=DEFAULT_PORT)
    server.start()