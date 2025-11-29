import threading
import cv2
import wx


class InitCameraThread(threading.Thread):
    """
    A background thread responsible for initializing the camera.
    It tries multiple backends to improve compatibility across devices.
    When done, it notifies the parent UI frame via wx.CallAfter().
    """

    def __init__(self, parent_frame):
        """
        :param parent_frame: The StoryCameraFrame instance that receives callbacks.
        """
        super().__init__(daemon=True)
        self.parent_frame = parent_frame
        self.start()

    def run(self):
        """
        Attempt to initialize the camera using different backends.
        If camera fails to open, trigger the UI's on_camera_fail().
        If successful, configure camera properties and call on_camera_ready().
        """
        camera = None
        backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
        # Try each backend until one works
        for backend in backends:
            try:
                camera = cv2.VideoCapture(0, backend)
                if camera.isOpened():
                    break
                # Release camera if backend failed
                camera.release()
            except cv2.error:
                # Ignore failure for this backend and try the next one
                pass

        # If camera is still not opened → report failure
        if not camera or not camera.isOpened():
            wx.CallAfter(self.parent_frame.on_camera_fail)
            return

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        wx.CallAfter(self.parent_frame.on_camera_ready, camera)
