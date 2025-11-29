import threading
import time
import base64
import cv2
import os
import wx

UPLOAD_PREPARE_DELAY_SECONDS = 1


class UploadThread(threading.Thread):
    """
    A background thread responsible for preparing and uploading media (photo or video)
    without freezing the UI. It handles Base64 encoding and then triggers the callback
    in the main UI thread.
    """
    def __init__(self, frame_ref, video_path, caption, media_type, callback, parent_frame):
        """Initialize the upload thread."""
        super().__init__(daemon=True)
        self.frame_ref = frame_ref
        self.video_path = video_path
        self.caption = caption
        self.media_type = media_type
        self.callback = callback
        self.parent_frame = parent_frame
        self.start()

    def run(self):
        """Main thread execution: encode media → send callback → notify success."""
        time.sleep(UPLOAD_PREPARE_DELAY_SECONDS)
        media_data = ""

        if self.media_type == "photo" and self.frame_ref is not None:
            ret, buf = cv2.imencode(".jpg", self.frame_ref)
            if ret:
                # Convert encoded JPG bytes to Base64 string
                media_data = base64.b64encode(buf).decode("utf-8")

        elif self.media_type == "video" and self.video_path and os.path.exists(self.video_path):
            try:
                # Open the video file as raw bytes
                with open(self.video_path, "rb") as f:
                    media_data = base64.b64encode(f.read()).decode("utf-8")
            except Exception as e:
                # Notify the UI about failure (must happen on main thread)
                wx.CallAfter(self.parent_frame.post_failed, f"Video Error: {e}")
                return

        if self.callback:
            # Call on_post_callback in the UI thread
            wx.CallAfter(self.callback, self.caption, self.media_type, media_data)

        wx.CallAfter(self.parent_frame.post_successful, self.media_type)
