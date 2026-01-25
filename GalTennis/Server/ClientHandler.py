"""
Gal Haham
Client Handler
Manages individual client streaming sessions
"""
import time
from VideoStreamManager import VideoStreamManager
from AudioStreamManager import AudioStreamManager
from NetworkManager import NetworkManager

INITIAL_FRAME_COUNT = 0
FRAME_INCREMENT_STEP = 1


class ClientHandler:
    """
    Handles streaming to a single client:
    - Coordinates video and audio streaming
    - Manages synchronization between video frames and audio chunks
    - Handles client disconnection and cleanup
    """

    def __init__(self, video_path, client_socket, address):
        self.video_path = video_path
        self.client_socket = client_socket
        self.address = address

        self.video_manager = VideoStreamManager(video_path)
        self.audio_manager = AudioStreamManager(video_path)

    def handle_streaming(self):
        """Main method to orchestrate the streaming process."""
        try:
            # 1. Setup Video
            if not self.video_manager.open_video():
                print(f"Failed to open video for client {self.address}")
                NetworkManager.close_client_socket(self.client_socket)
                return

            video_info = self.video_manager.get_video_info()

            # 2. Setup Audio
            self.audio_manager.setup_audio_extraction(video_info['fps'])

            # 3. Send Stream Info (Handshake)
            self._send_handshake(video_info)

            # 4. Main Streaming Loop
            self._stream_loop(video_info)

        except (ConnectionResetError, BrokenPipeError):
            print(f"Client {self.address} disconnected")
        except Exception as e:
            print(f"Error with client {self.address}: {e}")
        finally:
            self._cleanup()

    def _send_handshake(self, video_info):
        """Sends initial stream information to the client."""
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

        NetworkManager.send_stream_info(self.client_socket, stream_info)

        print(f"Streaming to {self.address}")
        print(
            f"   Video: {video_info['width']}x{video_info['height']} "
            f"@ {video_info['fps']: .2f} FPS"
        )
        print(
            f"   Audio: {audio_info['audio_sample_rate']} Hz, "
            f"{audio_info['audio_channels']} ch"
        )

    def _stream_loop(self, video_info):
        """Main loop for streaming video and audio frames - REFACTORED."""
        # Initialize streaming state
        streaming_state = self._initialize_streaming_state(video_info)

        # Main streaming loop
        while True:
            # Process one frame
            if not self._process_single_frame(streaming_state):
                break  # End of stream

            # Update frame counter
            streaming_state['frame_count'] += FRAME_INCREMENT_STEP

    def _initialize_streaming_state(self, video_info):
        """Initialize all state variables needed for streaming."""
        return {
            'frame_count': INITIAL_FRAME_COUNT,
            'start_time': time.time(),
            'frame_delay': video_info['frame_delay'],
            'total_frames': video_info['total_frames']
        }

    def _process_single_frame(self, state):
        """
        Process and send a single frame with audio.
        Returns True if successful, False if stream ended.
        """
        frame_start = time.time()

        # Read video frame
        ret, frame = self._read_video_frame()
        if not ret:
            self._print_stream_completion(state['frame_count'])
            return False

        # Read audio chunk
        audio_chunk = self._read_audio_chunk()

        # Send packet to client
        self._send_frame_packet(frame, audio_chunk, state['frame_count'])

        # Log progress
        self._log_streaming_progress(state)

        # Control frame rate
        self._control_frame_timing(frame_start, state['frame_delay'])

        return True

    def _read_video_frame(self):
        """Read the next video frame from video manager."""
        return self.video_manager.read_frame()

    def _read_audio_chunk(self):
        """Read the next audio chunk from audio manager."""
        return self.audio_manager.read_audio_chunk()

    def _send_frame_packet(self, frame, audio_chunk, frame_number):
        """Create and send a packet containing frame and audio."""
        packet = {
            'frame': frame,
            'audio': audio_chunk,
            'frame_number': frame_number
        }
        NetworkManager.send_packet(self.client_socket, packet)

    def _print_stream_completion(self, frame_count):
        """Print completion message when stream ends."""
        print(
            f"Finished streaming to {self.address} "
            f"({frame_count} frames)"
        )

    def _log_streaming_progress(self, state):
        """Log progress periodically during streaming."""
        VideoStreamManager.log_progress(
            state['frame_count'],
            state['total_frames'],
            state['start_time'],
            self.address
        )

    def _control_frame_timing(self, frame_start, frame_delay):
        """Control frame rate to maintain consistent timing."""
        VideoStreamManager.control_frame_rate(frame_start, frame_delay)

    def _cleanup(self):
        """Releases all resources for this client."""
        self.video_manager.close()
        self.audio_manager.close()
        NetworkManager.close_client_socket(self.client_socket)
        print(f"Connection closed: {self.address}")
