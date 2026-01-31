"""
Gal Haham
Background thread for Base64 encoding and story upload processing.
Prevents UI blocking during media file encoding operations.
"""
import threading
import time
import os
import base64
import cv2
import wx
INITIAL_DELAY_SECONDS = 1


class UploadThread(threading.Thread):
    """
    Handles the slow Base64 encoding and I/O operations in a separate thread
    when posting the story.
    """

    def __init__(self,
                 frame_ref,
                 video_path,
                 caption,
                 media_type,
                 callback,
                 parent_frame):
        """Initializes the upload worker thread and immediately starts it."""
        super().__init__(daemon=True)
        self.frame_ref = frame_ref
        self.video_path = video_path
        self.caption = caption
        self.media_type = media_type
        self.callback = callback
        self.parent_frame = parent_frame
        self.start()

    def run(self):
        """Performs media encoding in a background thread."""
        time.sleep(INITIAL_DELAY_SECONDS)
        media_data = ""

        if self.media_type == 'photo' and self.frame_ref is not None:
            ret, buf = cv2.imencode('.jpg', self.frame_ref)
            if ret:
                media_data = base64.b64encode(buf).decode('utf-8')

        elif (self.media_type == 'video' and
              self.video_path and
              os.path.exists(self.video_path)):
            try:
                with open(self.video_path, 'rb') as f:
                    media_data = base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                wx.CallAfter(
                    self.parent_frame.post_failed,
                    f"Video Read Error: {e}"
                )
                return

        if self.callback:
            wx.CallAfter(
                self.callback,
                self.caption,
                self.media_type,
                media_data
            )

        wx.CallAfter(
            self.parent_frame.post_successful,
            self.media_type
        )
