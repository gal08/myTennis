import wx
import cv2
import os
import time
import subprocess
import sys
from Audio_Recorder import AudioRecorder

from StoryCamera.InitCameraThread import InitCameraThread
from StoryCamera.CameraReaderThread import CameraReaderThread
from StoryCamera.UploadThread import UploadThread

SECONDS_IN_MINUTE = 60


class StoryCameraFrame(wx.Frame):
    """
        StoryCameraFrame
        ----------------
        A complete UI window that allows the user to create a "story" in the app,
        similar to stories in Instagram / Snapchat.

        This class provides:
            • Live camera preview using OpenCV
            • Ability to take a photo
            • Ability to record a 15-second video with audio
            • Preview mode (photo/video) before uploading
            • Upload thread that handles sending media back to the client
            • Graceful camera initialization and shutdown  """
    def __init__(self, parent, username, on_post_callback, closed_callback):
        """
            Constructor – initializes the entire story camera window.

            Initializes:
                • User state (username, callbacks)
                • Camera state variables
                • Recording state (video + audio)
                • UI components
                • Background camera initialization thread

            The window is:
                - Sized to a fixed mobile-like layout
                - Non-resizable (better UX)
                - Black themed for a clean modern look
        """
        super().__init__(parent, title="Create Story", size=wx.Size(480, 750),
                         style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self.username = username
        self.on_post_callback = on_post_callback
        self.closed_callback = closed_callback
        self.camera = None
        self.camera_reader_thread = None
        self.is_capturing = False
        self._current_frame_cache = None
        self.mode = 'photo'
        self.captured_photo = None
        self.preview_image = None
        self.is_recording = False
        self.video_writer = None
        self.temp_video_path = None
        self.audio_recorder = AudioRecorder()
        self.temp_audio_path = os.path.join(os.getcwd(), "story_audio.wav")
        self.final_video_path = os.path.join(os.getcwd(), "story_final.mp4")
        self.recording_start_time = None
        self.max_video_duration = 15
        self.preview_mode = False
        self.preview_type = None
        self.capture_enabled = False
        self.button_expanded = False
        self.button_size = 70

        self.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.init_ui()
        self.Centre()
        #self.Show()
        InitCameraThread(self)

    def init_ui(self):
        """
            Builds the full camera UI, which includes:

            1. Header section:
                - Close button
                - Title text ("Initializing Camera...")

            2. Camera preview panel:
                - Shows live frames from the camera
                - Shows a "loading camera" message until ready

            3. Recording indicator:
                - Red bar + timer when video recording is active

            4. Mode selector:
                - PHOTO / VIDEO toggle

            5. Capture button:
                - Circular UI with inner/outer rings
                - Handles taking photos / starting-stopping video recording

            6. Preview panel:
                - Appears after a photo/video is captured
                - Allows: Watch Video / Retake / Post Story

            The window uses wx.Timer (33 ms) to refresh the camera frame.
        """
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


    def on_camera_ready(self, camera):
        """
            Called when InitCameraThread successfully opens the camera.
            - Stores camera object
            - Starts the CameraReaderThread for continuous frame capture
            - Updates UI from "loading" → "Take Photo"
            - Enables capture actions
        """
        self.camera = camera
        self.is_capturing = True
        self.camera_reader_thread = CameraReaderThread(self.camera)
        self.title_text.SetLabel("Take Photo")
        self.loading_text.Hide()
        self.capture_enabled = True
        self.camera_panel.Refresh()

    def on_camera_fail(self):
        """
           Called when the camera cannot be opened.
           - Shows an error message
           - Calls the close handler (UI fallback)
        """
        self.is_capturing = False
        self.title_text.SetLabel("Camera Error")
        self.loading_text.SetLabel(" Failed to open camera")
        wx.MessageBox("Failed to open camera. Check if camera is in use.", "Error", wx.OK | wx.ICON_ERROR)
        self.on_close(None)

    def update_frame(self, event):
        """
            Timer callback (runs ~30 FPS).
            - Gets latest frame from CameraReaderThread
            - Updates cached frame for display
            - If video recording is active:
                    • Writes frame to video file
                    • Updates recording timer
                    • Stops automatically after max_video_duration
            - Refreshes camera panel so on_paint() redraws frame
        """
        if not self.preview_mode and self.is_capturing and self.camera_reader_thread:
            frame = self.camera_reader_thread.get_frame()
            if frame is not None:
                self._current_frame_cache = frame
                if self.is_recording and self.video_writer:
                    self.video_writer.write(frame)
                    elapsed = time.time() - self.recording_start_time
                    mins = int(elapsed // SECONDS_IN_MINUTE)
                    secs = int(elapsed % SECONDS_IN_MINUTE)
                    self.recording_timer.SetLabel(f"{mins}:{secs:02d}")
                    if elapsed >= self.max_video_duration:
                        self.stop_recording()
                self.camera_panel.Refresh()

    def on_paint(self, event):
        """
            Paint event for the camera preview panel.

            Behavior:
                - If in preview mode → draw the saved photo/video frame
                - Otherwise → draw the live camera frame

            Steps:
                1. Convert BGR → RGB (OpenCV → wxPython)
                2. Scale to fit the window while preserving aspect ratio
                3. Draw frame at center of the panel
        """
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
        """
            Paints the circular capture button:
                - Outer white ring
                - Inner red circle
                - Grows/shrinks when entering/exiting video mode
        """
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
        """Handles the main capture button behavior for both photo and video modes.

    Behavior:
    ---------
    1. If capturing is disabled (camera not ready), the function exits.
    2. If the current mode is 'photo':
           - Captures a single frame and enters preview mode.
    3. If the mode is 'video':
           - First click: expand the button and start video + audio recording.
           - Second click: shrink the button and stop recording, then show preview.

    Button expansion/shrink is a visual indicator for recording state:
        - Expanded  → Recording started
        - Normal    → Recording stopped

    After updating the recording state, the button area is refreshed
    so the UI immediately displays the updated button size.
    """
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

    def switch_mode(self, mode):
        """
            Switch between PHOTO and VIDEO modes.
            Updates button colors + UI text accordingly.
        """
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
        """
            Captures the current camera frame:
                - Stores it in self.captured_photo
                - Converts to display bitmap
                - Enters preview mode
        """
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

    def start_recording(self):
        """
            Starts recording:
                - Creates video writer (OpenCV)
                - Starts audio recording thread
                - Shows recording indicator + timer
        """
        if self._current_frame_cache is None or self.is_recording:
            return

        # start video
        self.temp_video_path = os.path.join(os.getcwd(), "story.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        h, w = self._current_frame_cache.shape[:2]
        self.video_writer = cv2.VideoWriter(self.temp_video_path, fourcc, 20.0, (w, h))

        # start audio
        self.audio_recorder.start_recording()

        self.is_recording = True
        self.recording_start_time = time.time()
        self.recording_indicator.Show()

    def stop_recording(self):
        """
            Stops recording:
                - Finalizes video writer
                - Stops audio recorder
                - Saves audio file
                - Merges audio + video via FFmpeg
                - Loads screenshot frame for preview mode
            """
        if not self.is_recording:
            return

        self.is_recording = False
        self.recording_indicator.Hide()

        # stop video
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        # stop audio
        self.audio_recorder.stop_recording()
        self.audio_recorder.save_audio(self.temp_audio_path)

        # merge audio + video
        self.merge_audio_video()

        # show preview from final video
        frame = cv2.VideoCapture(self.final_video_path).read()[1]
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]
            panel_size = self.camera_panel.GetSize()
            scale = min(panel_size.width / w, panel_size.height / h)
            new_w, new_h = int(w * scale), int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h))
            self.preview_image = wx.Bitmap(wx.Image(new_w, new_h, frame.tobytes()))

        self.preview_type = 'video'
        self.enter_preview_mode()

    def merge_audio_video(self):
        """
            Uses FFmpeg to merge:
                video: story.mp4
                audio: story_audio.wav
            Output → story_final.mp4

            FFmpeg command:
                ffmpeg -y -i video.mp4 -i audio.wav -c:v copy -c:a aac output.mp4
            """
        output = self.final_video_path

        cmd = [
            "ffmpeg",
            "-y",
            "-i", self.temp_video_path,
            "-i", self.temp_audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            output
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


    def enter_preview_mode(self):
        """Switches UI into preview mode (photo/video review screen)."""
        self.preview_mode = True
        self.camera_panel.Hide()
        self.preview_panel.Show()
        self.main_sizer.Layout()

    def exit_preview_mode(self):
        """Returns to camera mode and clears preview state."""
        self.preview_mode = False
        self.camera_panel.Show()
        self.preview_panel.Hide()
        self.preview_image = None
        self.preview_type = None
        self.main_sizer.Layout()
        self.camera_panel.Refresh()

    def on_retake(self, event):
        """
            Handles the 'Retake' action in preview mode.

            When the user decides they do not want to keep the captured
            photo/video, this method:
                - Exits preview mode
                - Returns the UI back to live camera mode
                - Clears the previously captured frame(s)
        """
        self.exit_preview_mode()

    def on_watch_video(self, event):
        """Opens the recorded video file using the operating system's default player.

    Behavior:
        - Only works when previewing a video (not a photo)
        - Verifies that the final video file exists
        - Uses OS-specific commands to open the video:
              • Windows → os.startfile()
              • macOS   → open
              • Linux   → xdg-open

    This allows the user to watch the recorded video before posting it."""
        if self.preview_type != 'video' or not os.path.exists(self.temp_video_path):
            return
        if sys.platform.startswith('win'):
            os.startfile(self.temp_video_path)
        elif sys.platform.startswith('darwin'):
            subprocess.call(('open', self.temp_video_path))
        else:
            subprocess.call(('xdg-open', self.temp_video_path))

    def on_post(self, event):
        """
            Sends the captured media (photo/video) to UploadThread.
            UploadThread returns base64 data to on_post_callback.
            """
        if self.preview_type == 'photo' and self.captured_photo is not None:
            UploadThread(self.captured_photo, None, "", 'photo', self.on_post_callback, self)
        elif self.preview_type == 'video' and self.temp_video_path:
            UploadThread(None, self.final_video_path, "", 'video', self.on_post_callback, self)
        else:
            wx.MessageBox("No media to post.", "Error", wx.OK | wx.ICON_ERROR)

    def post_successful(self, media_type):
        """
            Called when UploadThread finishes successfully.
            Shows success message and resets preview mode.
            """
        wx.MessageBox(f"{media_type.capitalize()} posted successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
        self.on_retake(None)

    def post_failed(self, message):
        """Shows an error message if upload fails."""
        wx.MessageBox(f"Failed to post: {message}", "Error", wx.OK | wx.ICON_ERROR)

    def on_close(self, event):
        """
            Gracefully shuts down:
                - Stops reader thread
                - Releases camera
                - Stops timer
                - Destroys OpenCV windows
                - Calls closed_callback
                - Closes the frame and exits wx MainLoop

            Ensures no camera lock or zombie threads remain.
            """
        print("Closing camera...")

        if self.camera_reader_thread:
            self.camera_reader_thread.stop()
            self.camera_reader_thread.join(timeout=1)

        if self.camera and self.camera.isOpened():
            self.camera.release()

        if hasattr(self, 'timer') and self.timer.IsRunning():
            self.timer.Stop()

        cv2.destroyAllWindows()

        if self.closed_callback:
            self.closed_callback()

        self.Destroy()

        wx.GetApp().ExitMainLoop()