import threading
import cv2
import wx

PRIMARY_CAMERA = 0
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
VIDEO_FPS = 30
LOW_LATENCY_BUFFER = 1
"""
Gal Haham
Background thread for camera initialization using multiple OpenCV backends.
Prevents UI freeze during camera setup and notifies
parent frame on success/failure.
"""


class InitCameraThread(threading.Thread):
    """
    Runs camera initialization in a separate
     background thread to avoid UI freeze.

    Responsibilities:
    - Open the webcam using different OpenCV backends.
    - Prevent the main UI (wxPython) from blocking during initialization.
    - On success: return the initialized cv2.VideoCapture object.
    - On failure: notify the parent UI that camera initialization failed.
    """

    def __init__(self, parent_frame):
        super().__init__(daemon=True)
        self.parent_frame = parent_frame
        self.start()

    def run(self):
        """Attempts to open the default system camera
        using multiple OpenCV backends."""
        print("[DEBUG InitCamera] Starting camera initialization...")
        camera = None
        backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]

        for backend in backends:
            try:
                print(f"[DEBUG InitCamera] Trying backend: {backend}")
                camera = cv2.VideoCapture(PRIMARY_CAMERA, backend)
                if camera.isOpened():
                    print(
                        f"[DEBUG InitCamera] Success with backend {backend}!"
                    )
                    break
                camera.release()
            except Exception as e:
                print(f"[DEBUG InitCamera] Failed with backend {backend}: {e}")
                pass

        if not camera or not camera.isOpened():
            print("[DEBUG InitCamera] All backends failed!")
            wx.CallAfter(self.parent_frame.on_camera_fail)
            return

        print("[DEBUG InitCamera] Setting camera properties...")
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, DEFAULT_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, DEFAULT_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS, VIDEO_FPS)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, LOW_LATENCY_BUFFER)

        print("[DEBUG InitCamera] Camera ready, calling on_camera_ready")
        wx.CallAfter(self.parent_frame.on_camera_ready, camera)