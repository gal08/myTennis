import wx
import cv2
import base64
import threading
import numpy as np
import time
import os
import subprocess
import sys

from Audio_Recorder import AudioRecorder  # 🔊 מוסיף מחלקת אודיו


# =======================================================================
# 1. INIT CAMERA THREAD
# =======================================================================
class InitCameraThread(threading.Thread):
    def __init__(self, parent_frame):
        super().__init__(daemon=True)
        self.parent_frame = parent_frame
        self.start()

    def run(self):
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

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        wx.CallAfter(self.parent_frame.on_camera_ready, camera)


# =======================================================================
# 2. CAMERA READER THREAD
# =======================================================================
class CameraReaderThread(threading.Thread):
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
# 3. UPLOAD THREAD
# =======================================================================
class UploadThread(threading.Thread):
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
        time.sleep(1)
        media_data = ""
        if self.media_type == 'photo' and self.frame_ref is not None:
            ret, buf = cv2.imencode('.jpg', self.frame_ref)
            if ret:
                media_data = base64.b64encode(buf).decode('utf-8')
        elif self.media_type == 'video' and self.video_path and os.path.exists(self.video_path):
            try:
                with open(self.video_path, 'rb') as f:
                    media_data = base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                wx.CallAfter(self.parent_frame.post_failed, f"Video Read Error: {e}")
                return
        if self.callback:
            wx.CallAfter(self.callback, self.caption, self.media_type, media_data)
        wx.CallAfter(self.parent_frame.post_successful, self.media_type)


# =======================================================================
# 4. STORY CAMERA FRAME (UI + AUDIO + MERGE)
# =======================================================================
class StoryCameraFrame(wx.Frame):
    def __init__(self, parent, username, on_post_callback, closed_callback):
        super().__init__(parent, title="Create Story", size=wx.Size(480, 750),
                         style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self.username = username
        self.on_post_callback = on_post_callback
        self.closed_callback = closed_callback

        # CAMERA STATE
        self.camera = None
        self.camera_reader_thread = None
        self.is_capturing = False
        self._current_frame_cache = None
        self.mode = 'photo'
        self.captured_photo = None
        self.preview_image = None

        # VIDEO RECORDING
        self.is_recording = False
        self.video_writer = None
        self.temp_video_path = None        # וידאו גולמי מהמצלמה
        self.recording_start_time = None
        self.max_video_duration = 15
        self.preview_mode = False
        self.preview_type = None
        self.capture_enabled = False
        self.button_expanded = False
        self.button_size = 70

        # AUDIO RECORDING
        self.audio_recorder = None
        self.audio_path = os.path.join(os.getcwd(), "story_audio.wav")
        self.final_video_path = None       # וידאו אחרי מיזוג אודיו+וידאו

        self.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.init_ui()
        self.Centre()
        self.Show()
        InitCameraThread(self)

    # ===================================================================
    # UI INIT
    # ===================================================================
    def init_ui(self):
        main_panel = wx.Panel(self)
        main_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # HEADER
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

        # CAMERA PANEL
        self.camera_panel = wx.Panel(main_panel, size=(-1, 500))
        self.camera_panel.SetBackgroundColour(wx.Colour(30, 30, 30))
        self.main_sizer.Add(self.camera_panel, 1, wx.EXPAND | wx.ALL, 0)

        self.loading_text = wx.StaticText(self.camera_panel, label=" Loading Camera...", pos=(150, 230))
        self.loading_text.SetForegroundColour(wx.Colour(200, 200, 200))
        self.loading_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        # RECORDING INDICATOR
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

        # MODE SELECTOR
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

        # CAPTURE BUTTON
        self.controls_panel = wx.Panel(main_panel)
        self.controls_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        controls_sizer.AddStretchSpacer()
        self.button_container = wx.Panel(self.controls_panel, size=(100, 100))
        self.button_container.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.button_container.Bind(wx.EVT_PAINT, self.on_paint_button)
        self.button_container.Bind(wx.EVT_LEFT_DOWN, self.on_button_click)
        controls_sizer.Add(self.button_container, 0, wx.ALIGN_CENTER_VERTICAL)
        controls_sizer.AddStretchSpacer()
        self.controls_panel.SetSizer(controls_sizer)
        self.main_sizer.Add(self.controls_panel, 0, wx.EXPAND | wx.ALL, 15)

        # PREVIEW PANEL
        self.preview_panel = wx.Panel(main_panel)
        self.preview_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        preview_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.watch_video_btn = wx.Button(self.preview_panel, label="Watch Video", size=(120, 45))
        self.watch_video_btn.SetBackgroundColour(wx.Colour(0, 120, 215))
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

        post_btn = wx.Button(self.preview_panel, label="Post Story", size=(120, 45))
        post_btn.SetBackgroundColour(wx.Colour(76, 175, 80))
        post_btn.SetForegroundColour(wx.WHITE)
        post_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        post_btn.Bind(wx.EVT_BUTTON, self.on_post)
        preview_sizer.Add(post_btn, 0, wx.ALL, 10)
        preview_sizer.AddStretchSpacer()
        self.preview_panel.SetSizer(preview_sizer)
        self.preview_panel.Hide()
        self.main_sizer.Add(self.preview_panel, 0, wx.EXPAND | wx.ALL, 5)

        main_panel.SetSizer(self.main_sizer)
        self.camera_panel.Bind(wx.EVT_PAINT, self.on_paint)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_frame, self.timer)
        self.timer.Start(33)

    # ===================================================================
    # CAMERA CALLBACKS
    # ===================================================================
    def on_camera_ready(self, camera):
        self.camera = camera
        self.is_capturing = True
        self.camera_reader_thread = CameraReaderThread(self.camera)
        self.title_text.SetLabel("Take Photo")
        self.loading_text.Hide()
        self.capture_enabled = True
        self.camera_panel.Refresh()

    def on_camera_fail(self):
        self.is_capturing = False
        self.title_text.SetLabel("Camera Error")
        self.loading_text.SetLabel(" Failed to open camera")
        wx.MessageBox("Failed to open camera. Check if camera is in use.", "Error", wx.OK | wx.ICON_ERROR)
        self.on_close(None)

    # ===================================================================
    # FRAME UPDATE & PAINT
    # ===================================================================
    def update_frame(self, event):
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
        dc = wx.PaintDC(self.button_container)
        gc = wx.GraphicsContext.Create(dc)
        if gc:
            gc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
            gc.DrawRectangle(0, 0, 100, 100)
            center_x, center_y = 50, 50
            outer_size = self.button_size
            gc.SetBrush(wx.Brush(wx.Colour(255, 255, 255)))
            gc.DrawEllipse(center_x - outer_size / 2, center_y - outer_size / 2, outer_size, outer_size)
            inner_size = outer_size * 0.7
            gc.SetBrush(wx.Brush(wx.Colour(255, 50, 80)))
            gc.DrawEllipse(center_x - inner_size / 2, center_y - inner_size / 2, inner_size, inner_size)

    def on_button_click(self, event):
        if not self.capture_enabled or not self.is_capturing:
            return
        if self.mode == 'photo':
            self.capture_photo()
        elif self.mode == 'video':
            if not self.button_expanded:
                self.button_expanded = True
                self.button_size = 85
                self.start_recording()
            else:
                self.button_expanded = False
                self.button_size = 70
                self.stop_recording()
            self.button_container.Refresh()

    # ===================================================================
    # PHOTO / VIDEO MODE
    # ===================================================================
    def switch_mode(self, mode):
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
        if self._current_frame_cache is None:
            return
        self.captured_photo = self._current_frame_cache.copy()
        frame = cv2.cvtColor(self.captured_photo, cv2.COLOR_BGR2RGB)
        h, w = frame.shape[:2]
        panel_size = self.camera_panel.GetSize()
        scale = min(panel_size.width / w, panel_size.height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h))
        self.preview_image = wx.Bitmap(wx.Image(new_w, new_h, frame.tobytes()))
        self.preview_type = 'photo'
        self.enter_preview_mode()

    # ===================================================================
    # RECORDING VIDEO + AUDIO
    # ===================================================================
    def start_recording(self):
        if self._current_frame_cache is None or self.is_recording:
            return

        # path לוידאו גולמי
        self.temp_video_path = os.path.join(os.getcwd(), "story_raw.mp4")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        h, w = self._current_frame_cache.shape[:2]
        self.video_writer = cv2.VideoWriter(self.temp_video_path, fourcc, 20.0, (w, h))

        # התחלת הקלטת אודיו
        self.audio_recorder = AudioRecorder()
        self.audio_recorder.start_recording()

        self.is_recording = True
        self.recording_start_time = time.time()
        self.recording_indicator.Show()

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        self.recording_indicator.Hide()

        # עצירת וידאו
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        # עצירת אודיו ושמירה ל-WAV
        if self.audio_recorder:
            self.audio_recorder.stop_recording()
            self.audio_recorder.save_audio(self.audio_path)
            self.audio_recorder.cleanup()
            self.audio_recorder = None

        # יצירת פריים preview מוידאו גולמי
        frame_cap = cv2.VideoCapture(self.temp_video_path)
        ret, frame = frame_cap.read()
        frame_cap.release()
        if ret and frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]
            panel_size = self.camera_panel.GetSize()
            scale = min(panel_size.width / w, panel_size.height / h)
            new_w, new_h = int(w * scale), int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h))
            self.preview_image = wx.Bitmap(wx.Image(new_w, new_h, frame.tobytes()))

        # מיזוג אודיו + וידאו
        self.final_video_path = os.path.join(os.getcwd(), "story_final.mp4")
        merged_path = self.merge_audio_video(self.temp_video_path, self.audio_path, self.final_video_path)

        if merged_path is None:
            # אם ffmpeg נכשל – נ fallback לוידאו גולמי ללא אודיו
            self.final_video_path = self.temp_video_path

        self.preview_type = 'video'
        self.enter_preview_mode()

    def merge_audio_video(self, video_path, audio_path, output_path):
        """
        מיזוג וידאו + אודיו לקובץ MP4 אחד.
        דורש ffmpeg מותקן במערכת (ב-path).
        """
        if not os.path.exists(video_path):
            print("merge_audio_video: video file not found")
            return None

        # אם אין קובץ אודיו – נחזיר וידאו בלבד
        if not os.path.exists(audio_path):
            try:
                import shutil
                shutil.copy(video_path, output_path)
                return output_path
            except Exception as e:
                print("merge_audio_video: failed to copy video without audio:", e)
                return None

        command = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]

        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                print("ffmpeg error:", result.stderr.decode(errors='ignore'))
                # fallback – נחזיר את הוידאו המקורי
                return None
            return output_path
        except Exception as e:
            print("merge_audio_video: exception while running ffmpeg:", e)
            return None

    # ===================================================================
    # PREVIEW MODE
    # ===================================================================
    def enter_preview_mode(self):
        self.preview_mode = True
        self.camera_panel.Hide()
        self.preview_panel.Show()
        self.main_sizer.Layout()

    def exit_preview_mode(self):
        self.preview_mode = False
        self.camera_panel.Show()
        self.preview_panel.Hide()
        self.preview_image = None
        self.preview_type = None
        self.main_sizer.Layout()
        self.camera_panel.Refresh()

    def on_retake(self, event):
        self.exit_preview_mode()

    def on_watch_video(self, event):
        if self.preview_type != 'video':
            return

        # נעדיף וידאו סופי עם אודיו, אם יש
        path_to_open = self.final_video_path if self.final_video_path and os.path.exists(self.final_video_path) \
            else self.temp_video_path

        if not path_to_open or not os.path.exists(path_to_open):
            return

        if sys.platform.startswith('win'):
            os.startfile(path_to_open)
        elif sys.platform.startswith('darwin'):
            subprocess.call(('open', path_to_open))
        else:
            subprocess.call(('xdg-open', path_to_open))

    # ===================================================================
    # POST STORY
    # ===================================================================
    def on_post(self, event):
        if self.preview_type == 'photo' and self.captured_photo is not None:
            UploadThread(self.captured_photo, None, "", 'photo', self.on_post_callback, self)
        elif self.preview_type == 'video' and self.final_video_path:
            UploadThread(None, self.final_video_path, "", 'video', self.on_post_callback, self)
        else:
            wx.MessageBox("No media to post.", "Error", wx.OK | wx.ICON_ERROR)

    def post_successful(self, media_type):
        wx.MessageBox(f"{media_type.capitalize()} posted successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
        self.on_retake(None)

    def post_failed(self, message):
        wx.MessageBox(f"Failed to post: {message}", "Error", wx.OK | wx.ICON_ERROR)

    # ===================================================================
    # CLOSE HANDLER
    # ===================================================================
    def on_close(self, event):
        if self.camera_reader_thread:
            self.camera_reader_thread.stop()
        if self.camera and self.camera.isOpened():
            self.camera.release()
        self.Destroy()
        if self.closed_callback:
            self.closed_callback()
