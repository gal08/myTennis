import threading
import time

# Delay between camera frame reads to prevent CPU overload
FRAME_READ_DELAY_SECONDS = 0.01


class CameraReaderThread(threading.Thread):
    """
    A background thread responsible for continuously reading frames
    from the camera without blocking the main UI thread.

    It safely stores the latest frame using a lock, allowing the UI
    to fetch it at any time.
    """
    def __init__(self, camera):
        """Initialize the frame reader thread."""
        super().__init__(daemon=True)
        self.camera = camera
        self.is_running = True
        self.current_frame = None
        self.lock = threading.Lock()
        self.start()

    def run(self):
        """
        Continuously read frames from the camera in the background.
        Stores only the most recent frame to reduce memory usage.
        """
        while self.is_running:
            ret, frame = self.camera.read()
            if ret:
                # Store the frame safely
                with self.lock:
                    self.current_frame = frame
            # Small delay to reduce CPU load
            time.sleep(FRAME_READ_DELAY_SECONDS)

    def stop(self):
        """
        Stop the camera reading loop safely.
        """
        self.is_running = False

    def get_frame(self):
        """Retrieve the latest available frame in a thread-safe manner."""
        with self.lock:
            return (
                self.current_frame.copy()
                if self.current_frame is not None
                else None
            )
