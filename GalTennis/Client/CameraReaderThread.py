"""
Gal Haham
Background thread for continuous camera frame reading.
Provides thread-safe access to the latest frame without blocking the GUI.
"""
import threading
import time
SHORT_SLEEP_SECONDS = 0.01


class CameraReaderThread(threading.Thread):
    """
    Continuously captures frames from the camera in a background thread.

    Responsibilities:
    - Read frames without blocking the main GUI thread.
    - Store the most recent frame in a thread-safe way.
    - Allow other parts of the program to fetch the latest frame at any time.
    - Run independently until stopped.
    """

    def __init__(self, camera):
        """Initializes the thread and starts capturing frames"""
        super().__init__(daemon=True)
        self.camera = camera
        self.is_running = True
        self.current_frame = None
        self.lock = threading.Lock()
        self.start()

    def run(self):
        """Thread loop: continuously reads frames from the camera."""
        while self.is_running:
            ret, frame = self.camera.read()
            if ret:
                with self.lock:
                    self.current_frame = frame
            time.sleep(SHORT_SLEEP_SECONDS)

    def stop(self):
        """
        Stops the thread by setting the running flag to False.
        """
        self.is_running = False

    def get_frame(self):
        """Returns a copy of the most recent captured frame."""
        with self.lock:
            return (
                self.current_frame.copy()
                if self.current_frame is not None
                else None
            )
