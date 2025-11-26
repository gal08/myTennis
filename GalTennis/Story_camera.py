import wx
import cv2
import base64
import threading
import numpy as np
import time
from datetime import datetime
import tempfile
import os
import webbrowser
import sys
import subprocess


# =======================================================================
# 1. INIT CAMERA THREAD - OPTIMIZED
# =======================================================================

class InitCameraThread(threading.Thread):
    """
    Handles the blocking operation of cv2.VideoCapture(0) in a background thread
    to prevent the UI from freezing during initial load.
    """

    def __init__(self, parent_frame):
        super().__init__(daemon=True)
        self.parent_frame = parent_frame
        self.start()

    def run(self):
        # Try different backends for faster initialization
        camera = None
        backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]

        for backend in backends:
            try:
                camera = cv2.VideoCapture(0, backend)
                if camera.isOpened():
                    break
                camera.release()
            except:
                pass

        if not camera or not camera.isOpened():
            wx.CallAfter(self.parent_frame.on_camera_fail)
            return

        # Set properties
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        wx.CallAfter(self.parent_frame.on_camera_ready, camera)


# =======================================================================
# 2. CAMERA READER THREAD - OPTIMIZED
# =======================================================================

class CameraReaderThread(threading.Thread):
    """
    Reads frames from the camera continuously in a separate thread
    to prevent the UI from blocking during runtime.
    """

    def __init__(self, camera):
        super().__init__(daemon=True)
        self.camera = camera
        self.is_running = True
        self.current_frame = None
        self.lock = threading.Lock()
        self.start()

    def run(self):
        while self.is_running:
            ret, frame = self.camera.read()
            if ret:
                with self.lock:
                    self.current_frame = frame
            time.sleep(0.01)

    def stop(self):
        self.is_running = False

    def get_frame(self):
        with self.lock:
            return self.current_frame.copy() if self.current_frame is not None else None


# =======================================================================
# 3. UPLOAD THREAD - OPTIMIZED
# =======================================================================

class UploadThread(threading.Thread):
    """
    Handles the slow Base64 encoding and I/O operations in a separate thread
    when posting the story.
    """

    def __init__(self, frame_ref, video_path, caption, media_type, callback, parent_frame):
        super().__init__(daemon=True)
        self.frame_ref = frame_ref
        self.video_path = video_path
        self.caption = caption
        self.media_type = media_type
        self.callback = callback
        self.parent_frame = parent_frame
        self.start()

    def run(self):
        # Simulate heavy processing / network upload
        time.sleep(1)

        media_data = ""
        if self.media_type == 'photo' and self.frame_ref is not None:
            # Encode photo to base64 (simulation)
            ret, buf = cv2.imencode('.jpg', self.frame_ref)
            if ret:
                media_data = base64.b64encode(buf).decode('utf-8')

        elif self.media_type == 'video' and self.video_path and os.path.exists(self.video_path):
            # Read video file contents (simulation)
            try:
                with open(self.video_path, 'rb') as f:
                    media_data = base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                wx.CallAfter(self.parent_frame.post_failed, f"Video Read Error: {e}")
                return

        # הקריאה החוזרת מתבצעת כאן
        if self.callback:
            wx.CallAfter(self.callback, self.caption, self.media_type, media_data)

        wx.CallAfter(self.parent_frame.post_successful, self.media_type)


# =======================================================================
# 4. MAIN FRAME CLASS - OPTIMIZED
# =======================================================================

class StoryCameraFrame(wx.Frame):

    def __init__(self, parent, username, on_post_callback, closed_callback):
        super().__init__(
            parent,
            title="Create Story",
            size=wx.Size(480, 750),
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        )

        self.username = username
        self.on_post_callback = on_post_callback
        self.closed_callback = closed_callback

        # 🎯 הגדרת נתיב התיקייה הנוכחית של הקובץ המורץ
        if hasattr(sys, '_MEIPASS'):
            # אם מורץ כ-EXE, השתמש בנתיב הזמני של PyInstaller (פחות רלוונטי כאן)
            self.current_dir = sys._MEIPASS
        else:
            # אם מורץ כקובץ Python, השתמש בנתיב התיקייה של הקובץ הנוכחי
            self.current_dir = os.path.dirname(os.path.abspath(__file__))

        # Camera state
        self.camera = None
        self.camera_reader_thread = None
        self.is_capturing = False
        self._current_frame_cache = None

        # Mode state
        self.mode = 'photo'

        # Photo state
        self.captured_photo = None
        self.preview_image = None

        # Video state
        self.is_recording = False
        self.video_writer = None
        # נתיב לקובץ הזמני/הקבוע (story.mp4) בתיקייה הנוכחית
        self.temp_video_path = None
        self.recording_start_time = None
        self.max_video_duration = 15

        # Preview state
        self.preview_mode = False
        self.preview_type = None

        self.SetBackgroundColour(wx.Colour(0, 0, 0))

        # Initialize UI first (instant display)
        self.init_ui()

        # Show the window immediately
        self.Centre()
        self.Show()
        self.Update()

        # Start camera initialization in background
        InitCameraThread(self)

    def init_ui(self):
        """Initialize the camera UI - optimized for fast display"""
        main_panel = wx.Panel(self)
        main_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # ===== HEADER =====
        header_panel = wx.Panel(main_panel)
        header_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        close_btn = wx.Button(header_panel, label="X", size=(40, 40), style=wx.BORDER_NONE)
        close_btn.SetBackgroundColour(wx.Colour(50, 50, 50))
        close_btn.SetForegroundColour(wx.WHITE)
        close_btn.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        header_sizer.Add(close_btn, 0, wx.ALL, 10)
        header_sizer.AddStretchSpacer()

        self.title_text = wx.StaticText(header_panel, label="Initializing Camera...")
        self.title_text.SetForegroundColour(wx.WHITE)
        self.title_text.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        header_sizer.Add(self.title_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        header_sizer.AddStretchSpacer()
        header_sizer.AddSpacer(50)
        header_panel.SetSizer(header_sizer)
        self.main_sizer.Add(header_panel, 0, wx.EXPAND)

        # ===== CAMERA PREVIEW =====
        self.camera_panel = wx.Panel(main_panel, size=(-1, 500))
        self.camera_panel.SetBackgroundColour(wx.Colour(30, 30, 30))
        self.main_sizer.Add(self.camera_panel, 1, wx.EXPAND | wx.ALL, 0)

        # Loading indicator
        self.loading_text = wx.StaticText(self.camera_panel, label=" Loading Camera...",
                                          pos=(150, 230))
        self.loading_text.SetForegroundColour(wx.Colour(200, 200, 200))
        self.loading_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        # Recording indicator
        self.recording_indicator = wx.Panel(self.camera_panel, pos=(10, 10), size=(120, 35))
        self.recording_indicator.SetBackgroundColour(wx.Colour(220, 50, 50))
        rec_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rec_dot = wx.StaticText(self.recording_indicator, label="⬤")
        rec_dot.SetForegroundColour(wx.WHITE)
        rec_dot.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        rec_sizer.Add(rec_dot, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        self.recording_timer = wx.StaticText(self.recording_indicator, label="0:00")
        self.recording_timer.SetForegroundColour(wx.WHITE)
        self.recording_timer.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        rec_sizer.Add(self.recording_timer, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        self.recording_indicator.SetSizer(rec_sizer)
        self.recording_indicator.Hide()

        # ===== MODE SELECTOR =====
        mode_panel = wx.Panel(main_panel)
        mode_panel.SetBackgroundColour(wx.Colour(15, 15, 15))
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mode_sizer.AddStretchSpacer()
        self.photo_btn = wx.Button(mode_panel, label="PHOTO", size=(100, 35), style=wx.BORDER_NONE)
        self.photo_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.photo_btn.SetForegroundColour(wx.Colour(0, 0, 0))
        self.photo_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.photo_btn.Bind(wx.EVT_BUTTON, lambda e: self.switch_mode('photo'))
        mode_sizer.Add(self.photo_btn, 0, wx.ALL, 5)
        self.video_btn = wx.Button(mode_panel, label="VIDEO", size=(100, 35), style=wx.BORDER_NONE)
        self.video_btn.SetBackgroundColour(wx.Colour(50, 50, 50))
        self.video_btn.SetForegroundColour(wx.Colour(150, 150, 150))
        self.video_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.video_btn.Bind(wx.EVT_BUTTON, lambda e: self.switch_mode('video'))
        mode_sizer.Add(self.video_btn, 0, wx.ALL, 5)
        mode_sizer.AddStretchSpacer()
        mode_panel.SetSizer(mode_sizer)
        self.main_sizer.Add(mode_panel, 0, wx.EXPAND)

        # ===== CAPTURE CONTROLS =====
        self.controls_panel = wx.Panel(main_panel)
        self.controls_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        controls_sizer.AddStretchSpacer()

        # Create circular capture button
        self.button_container = wx.Panel(self.controls_panel, size=(100, 100))
        self.button_container.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.button_container.Bind(wx.EVT_PAINT, self.on_paint_button)
        self.button_container.Bind(wx.EVT_LEFT_DOWN, self.on_button_click)

        self.button_size = 70  # Normal size
        self.button_expanded = False
        self.capture_enabled = False

        controls_sizer.Add(self.button_container, 0, wx.ALIGN_CENTER_VERTICAL)
        controls_sizer.AddStretchSpacer()
        self.controls_panel.SetSizer(controls_sizer)
        self.main_sizer.Add(self.controls_panel, 0, wx.EXPAND | wx.ALL, 15)

        # ===== PREVIEW CONTROLS (NEW) =====
        self.preview_panel = wx.Panel(main_panel)
        self.preview_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        preview_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Button to watch the video
        self.watch_video_btn = wx.Button(self.preview_panel, label="Watch Video", size=(120, 45))
        self.watch_video_btn.SetBackgroundColour(wx.Colour(0, 120, 215))  # Dark blue
        self.watch_video_btn.SetForegroundColour(wx.WHITE)
        self.watch_video_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.watch_video_btn.Bind(wx.EVT_BUTTON, self.on_watch_video)
        preview_sizer.Add(self.watch_video_btn, 0, wx.ALL, 10)

        retake_btn = wx.Button(self.preview_panel, label="Retake", size=(120, 45))
        retake_btn.SetBackgroundColour(wx.Colour(50, 50, 50))
        retake_btn.SetForegroundColour(wx.WHITE)
        retake_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        retake_btn.Bind(wx.EVT_BUTTON, self.on_retake)
        preview_sizer.Add(retake_btn, 0, wx.ALL, 10)

        preview_sizer.AddStretchSpacer()

        post_btn = wx.Button(self.preview_panel, label="Post Story", size=(120, 45))
        post_btn.SetBackgroundColour(wx.Colour(76, 175, 80))
        post_btn.SetForegroundColour(wx.WHITE)
        post_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        post_btn.Bind(wx.EVT_BUTTON, self.on_post)
        preview_sizer.Add(post_btn, 0, wx.ALL, 10)
        self.preview_panel.SetSizer(preview_sizer)
        self.preview_panel.Hide()
        self.main_sizer.Add(self.preview_panel, 0, wx.EXPAND | wx.ALL, 5)

        main_panel.SetSizer(self.main_sizer)

        # Bind paint event and timer
        self.camera_panel.Bind(wx.EVT_PAINT, self.on_paint)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_frame, self.timer)
        self.timer.Start(33)

    def on_camera_ready(self, camera):
        """Called by InitCameraThread when camera is successfully opened."""
        self.camera = camera
        self.is_capturing = True
        self.camera_reader_thread = CameraReaderThread(self.camera)

        # Update UI
        self.title_text.SetLabel("Take Photo")
        self.loading_text.Hide()
        self.capture_enabled = True
        self.camera_panel.Refresh()

    def on_camera_fail(self):
        """Called by InitCameraThread on failure."""
        self.is_capturing = False
        self.title_text.SetLabel("Camera Error")
        self.loading_text.SetLabel(" Failed to open camera")
        wx.MessageBox("Failed to open camera. Check if camera is in use.", "Error", wx.OK | wx.ICON_ERROR)

        # Close and unblock Client.py on camera failure
        self.on_close(None)

    def update_frame(self, event):
        """Update camera preview - only runs if is_capturing is True."""
        if not self.preview_mode and self.is_capturing and self.camera_reader_thread:
            frame = self.camera_reader_thread.get_frame()

            if frame is not None:
                self._current_frame_cache = frame

                if self.is_recording and self.video_writer:
                    self.video_writer.write(frame)

                    elapsed = time.time() - self.recording_start_time
                    mins = int(elapsed // 60)
                    secs = int(elapsed % 60)
                    self.recording_timer.SetLabel(f"{mins}:{secs:02d}")

                    if elapsed >= self.max_video_duration:
                        self.stop_recording()

                self.camera_panel.Refresh()

    def on_paint(self, event):
        """Draw camera preview or preview image"""
        dc = wx.PaintDC(self.camera_panel)

        if self.preview_mode and self.preview_image:
            dc.DrawBitmap(self.preview_image, 0, 0)
        elif self._current_frame_cache is not None:
            frame = cv2.cvtColor(self._current_frame_cache, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]

            panel_size = self.camera_panel.GetSize()
            scale = min(panel_size.width / w, panel_size.height / h)
            new_w, new_h = int(w * scale), int(h * scale)

            frame = cv2.resize(frame, (new_w, new_h))
            image = wx.Image(new_w, new_h, frame.tobytes())
            bitmap = wx.Bitmap(image)

            x = (panel_size.width - new_w) // 2
            y = (panel_size.height - new_h) // 2

            dc.Clear()
            dc.DrawBitmap(bitmap, x, y)

    def on_paint_button(self, event):
        """Draw circular button"""
        dc = wx.PaintDC(self.button_container)
        gc = wx.GraphicsContext.Create(dc)

        if gc:
            # Clear background
            gc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
            gc.DrawRectangle(0, 0, 100, 100)

            # Draw outer white circle
            center_x, center_y = 50, 50
            outer_size = self.button_size

            gc.SetBrush(wx.Brush(wx.Colour(255, 255, 255)))
            gc.DrawEllipse(center_x - outer_size / 2, center_y - outer_size / 2, outer_size, outer_size)

            # Draw inner red circle or square
            if self.button_expanded and self.mode == 'video':
                # Recording - show red square
                inner_size = outer_size * 0.4
                gc.SetBrush(wx.Brush(wx.Colour(255, 50, 80)))
                gc.DrawRectangle(center_x - inner_size / 2, center_y - inner_size / 2, inner_size, inner_size)
            else:
                # Not recording - show red circle
                inner_size = outer_size * 0.7
                gc.SetBrush(wx.Brush(wx.Colour(255, 50, 80)))
                gc.DrawEllipse(center_x - inner_size / 2, center_y - inner_size / 2, inner_size, inner_size)

    def on_button_click(self, event):
        """Handle button click - toggle expand/collapse"""
        if not self.capture_enabled or not self.is_capturing:
            return

        if self.mode == 'photo':
            # Photo mode: just capture
            self.capture_photo()
        elif self.mode == 'video':
            # Video mode: toggle recording
            if not self.button_expanded:
                # Start recording
                self.button_expanded = True
                self.button_size = 85  # Expanded size
                self.start_recording()
            else:
                # Stop recording
                self.button_expanded = False
                self.button_size = 70  # Normal size
                self.stop_recording()

            self.button_container.Refresh()

    def switch_mode(self, mode):
        """Switch between photo and video mode"""
        self.mode = mode

        if mode == 'photo':
            self.photo_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.photo_btn.SetForegroundColour(wx.Colour(0, 0, 0))
            self.video_btn.SetBackgroundColour(wx.Colour(50, 50, 50))
            self.video_btn.SetForegroundColour(wx.Colour(150, 150, 150))
            self.title_text.SetLabel("Take Photo")
        else:
            self.video_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.video_btn.SetForegroundColour(wx.Colour(0, 0, 0))
            self.photo_btn.SetBackgroundColour(wx.Colour(50, 50, 50))
            self.photo_btn.SetForegroundColour(wx.Colour(150, 150, 150))
            self.title_text.SetLabel("Record Video (Click to Start/Stop)")

    def capture_photo(self):
        """Capture a single photo"""
        if self._current_frame_cache is None:
            return

        self.captured_photo = self._current_frame_cache.copy()

        frame = cv2.cvtColor(self.captured_photo, cv2.COLOR_BGR2RGB)
        h, w = frame.shape[:2]

        panel_size = self.camera_panel.GetSize()
        scale = min(panel_size.width / w, panel_size.height / h)
        new_w, new_h = int(w * scale), int(h * scale)

        frame = cv2.resize(frame, (new_w, new_h))
        image = wx.Image(new_w, new_h, frame.tobytes())
        self.preview_image = wx.Bitmap(image)

        self.preview_type = 'photo'
        self.enter_preview_mode()

    def start_recording(self):
        """Start video recording"""
        if self._current_frame_cache is None or self.is_recording:
            return

        # 🎯 יצירת קובץ זמני עם סיומת AVI בתיקייה הנוכחית
        temp_filename = "temp_story_" + str(int(time.time())) + ".avi"
        self.temp_video_path = os.path.join(self.current_dir, temp_filename)

        h, w = self._current_frame_cache.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        # שומרים את הקובץ הזמני בנתיב הנוכחי
        self.video_writer = cv2.VideoWriter(self.temp_video_path, fourcc, 30.0, (w, h))

        if not self.video_writer.isOpened():
            self.video_writer = None
            self.button_expanded = False
            self.button_size = 70
            self.button_container.Refresh()
            return

        self.is_recording = True
        self.recording_start_time = time.time()
        self.recording_indicator.Show()

    def stop_recording(self):
        """Stop video recording"""
        if not self.is_recording:
            return

        self.is_recording = False
        self.recording_indicator.Hide()

        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        wx.MilliSleep(200)

        if not os.path.exists(self.temp_video_path):
            wx.MessageBox("Failed to save video file", "Error", wx.OK | wx.ICON_ERROR)
            return

        # 🎯 שינוי שם הקובץ ל-story.mp4 בתיקייה הנוכחית
        temp_avi_path = self.temp_video_path
        permanent_video_path = os.path.join(self.current_dir, "story.mp4")

        try:
            # אם הקובץ הקבוע story.mp4 קיים, מחק אותו
            if os.path.exists(permanent_video_path):
                os.remove(permanent_video_path)

            # שנה את שם הקובץ הזמני לקובץ הקבוע
            os.rename(temp_avi_path, permanent_video_path)
            # עדכן את הנתיב הקבוע במשתנה, כך שכל פונקציה אחרת תשתמש בו
            self.temp_video_path = permanent_video_path

        except Exception as e:
            wx.MessageBox(f"Failed to rename video file: {e}", "Error", wx.OK | wx.ICON_ERROR)
            # אם נכשל, נשמור את הנתיב הזמני למקרה של צורך בניקוי
            self.temp_video_path = temp_avi_path
            return

        # Load first frame for preview
        # נשתמש בנתיב המעודכן (story.mp4)
        cap = cv2.VideoCapture(self.temp_video_path)
        ret, frame = cap.read()
        cap.release()

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]

            panel_size = self.camera_panel.GetSize()
            scale = min(panel_size.width / w, panel_size.height / h)
            new_w, new_h = int(w * scale), int(h * scale)

            frame = cv2.resize(frame, (new_w, new_h))
            image = wx.Image(new_w, new_h, frame.tobytes())
            self.preview_image = wx.Bitmap(image)

        self.preview_type = 'video'
        self.enter_preview_mode()

    def enter_preview_mode(self):
        """Switch to preview mode"""
        self.preview_mode = True
        self.controls_panel.Hide()
        self.preview_panel.Show()

        is_video = self.preview_type == 'video'
        self.watch_video_btn.Show(is_video)

        self.main_sizer.Layout()
        self.Layout()
        self.camera_panel.Refresh()

    def on_retake(self, event):
        """Return to camera mode"""
        self.preview_mode = False
        self.preview_image = None
        self.captured_photo = None
        self.button_expanded = False
        self.button_size = 70

        if self.temp_video_path and os.path.exists(self.temp_video_path):
            try:
                os.remove(self.temp_video_path)
            except:
                pass
            self.temp_video_path = None

        self.controls_panel.Show()
        self.preview_panel.Hide()
        self.button_container.Refresh()
        self.Layout()

    def on_watch_video(self, event):
        """פתיחת קובץ הווידאו שנשמר כ-story.mp4 לצפייה."""
        if self.preview_type != 'video' or not self.temp_video_path:
            wx.MessageBox("Video file not available for playback.", "Error", wx.OK | wx.ICON_ERROR)
            return

        # 🎯 שימוש בנתיב המעודכן (story.mp4) שנשמר בתיקייה הנוכחית
        video_path = self.temp_video_path

        if not os.path.exists(video_path):
            wx.MessageBox(f"File {os.path.basename(video_path)} not found for playback. Path: {video_path}", "Error",
                          wx.OK | wx.ICON_ERROR)
            return

        try:
            # שימוש ב-os.startfile או subprocess בהתאם למערכת ההפעלה
            if sys.platform.startswith("win"):
                os.startfile(video_path)
            elif sys.platform.startswith("darwin"):  # macOS
                subprocess.call(["open", video_path])
            else:  # Linux
                subprocess.call(["xdg-open", video_path])

        except Exception as e:
            wx.MessageBox(
                f"Failed to open video in local player: {e}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )

    def on_post(self, event):
        """Post media and save video as 'story.mp4' in the same folder."""
        caption_text = ""

        # ----- PHOTO -----
        if self.preview_type == 'photo' and self.captured_photo is not None:
            UploadThread(
                frame_ref=self.captured_photo,
                video_path=None,
                caption=caption_text,
                media_type='photo',
                callback=self.on_post_callback,
                parent_frame=self
            )
            wx.MessageBox("Starting photo upload in background...", "Uploading", wx.OK | wx.ICON_INFORMATION)
            self.on_close(None)
            return

        # ----- VIDEO -----
        elif (self.preview_type == 'video' and
              self.temp_video_path and
              os.path.exists(self.temp_video_path)):

            # הקובץ הוא כבר story.mp4 בנתיב הנכון
            new_video_path = self.temp_video_path

            UploadThread(
                frame_ref=None,
                video_path=new_video_path,
                caption=caption_text,
                media_type='video',
                callback=self.on_post_callback,
                parent_frame=self
            )

            wx.MessageBox("Starting video upload in background...", "Uploading", wx.OK | wx.ICON_INFORMATION)
            self.on_close(None)

        # ----- NO MEDIA -----
        else:
            wx.MessageBox(
                "No media captured or file missing.",
                "Error",
                wx.OK | wx.ICON_ERROR
            )

    def post_successful(self, media_type):
        """Called by UploadThread after successful upload"""
        pass  # Window already closed

    def post_failed(self, error_msg):
        """Called by UploadThread on failure"""
        wx.MessageBox(f"Failed to post story: {error_msg}", "Error", wx.OK | wx.ICON_ERROR)

    def on_close(self, event):
        """Clean up and close"""
        self.is_capturing = False
        self.timer.Stop()

        if self.is_recording:
            self.stop_recording()

        # ודא שהקובץ story.mp4 נשמר רק אם הוא נמצא בנתיב הנוכחי
        if self.temp_video_path and os.path.exists(self.temp_video_path) and 'story.mp4' in self.temp_video_path:
            # משאירים את story.mp4 בתיקייה הנוכחית
            pass

        elif self.temp_video_path and os.path.exists(self.temp_video_path):
            # אם מדובר בנתיב זמני כלשהו (למשל, AVI אם ה-rename נכשל), נמחק אותו
            try:
                os.remove(self.temp_video_path)
            except:
                pass

        # ... (שאר ניקוי המשתנים) ...

        if self.camera_reader_thread:
            self.camera_reader_thread.stop()

        if self.camera:
            self.camera.release()

        if self.video_writer:
            self.video_writer.release()

        self.temp_video_path = None  # ניקוי המשתנה

        # Execute the closed_callback to unblock Client.py
        if self.closed_callback:
            self.closed_callback()

        self.Destroy()


# =======================================================================
# 5. TEST EXECUTION BLOCK
# =======================================================================

if __name__ == '__main__':
    def test_callback(caption, media_type, media_data):
        print(f"Callback received data.")
        print(f"Caption: {caption}")
        print(f"Media Type: {media_type}")
        print(f"Media Data Length: {len(media_data)} characters")


    # Define closed_callback for standalone testing
    def closed_callback_func():
        print("Camera frame closed! Releasing console lock.")


    app = wx.App()
    # Pass the closed_callback function
    frame = StoryCameraFrame(None, "test_user", test_callback, closed_callback_func)
    app.MainLoop()