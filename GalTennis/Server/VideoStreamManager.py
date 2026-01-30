"""
Gal Haham
Video Stream Manager
Handles video file operations and frame streaming
"""
import cv2
import time

DEFAULT_FPS_FALLBACK = 30.0
INVALID_FPS_THRESHOLD = 0
SECONDS_PER_FRAME_CALCULATION_UNIT = 1.0
INITIAL_FRAME_COUNT = 0
FRAME_INCREMENT_STEP = 1
FRAME_COUNT_RESET_VALUE = 0
PROGRESS_LOG_EVERY_N_FRAMES = 30
MINIMUM_SLEEP_TIME_SECONDS = 0.0


class VideoStreamManager:
    """
    Manages video file operations including:
    - Opening video files
    - Extracting video information (fps, dimensions, frame count)
    - Reading and streaming video frames
    """

    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = None
        self.video_info = None

    def open_video(self):
        """Opens video file and extracts core video stream information."""
        self.cap = cv2.VideoCapture(self.video_path)

        if not self.cap.isOpened():
            print(f"Cannot open video: {self.video_path}")
            return False

        # Get video properties
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps <= INVALID_FPS_THRESHOLD:
            fps = DEFAULT_FPS_FALLBACK

        frame_delay = SECONDS_PER_FRAME_CALCULATION_UNIT / fps
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.video_info = {
            'fps': fps,
            'width': width,
            'height': height,
            'total_frames': total_frames,
            'frame_delay': frame_delay
        }

        return True

    def read_frame(self):
        """Reads the next frame from the video."""
        if not self.cap:
            return False, None

        ret, frame = self.cap.read()
        return ret, frame

    def get_video_info(self):
        """Returns the video information dictionary."""
        return self.video_info

    def close(self):
        """Releases the video capture resource."""
        if self.cap:
            self.cap.release()
            self.cap = None

    @staticmethod
    def control_frame_rate(frame_start, frame_delay):
        """Pauses execution to maintain the target frame rate."""
        elapsed = time.time() - frame_start
        sleep_time = max(
            MINIMUM_SLEEP_TIME_SECONDS,
            frame_delay - elapsed
        )
        if sleep_time > MINIMUM_SLEEP_TIME_SECONDS:
            time.sleep(sleep_time)

    @staticmethod
    def log_progress(frame_count, total_frames, start_time, address):
        """Logs streaming progress periodically."""
        if (frame_count % PROGRESS_LOG_EVERY_N_FRAMES ==
                FRAME_COUNT_RESET_VALUE):
            elapsed = time.time() - start_time
            print(
                f"Client {address}: Frame {frame_count}/"
                f"{total_frames} ({elapsed: .1f}s)"
            )