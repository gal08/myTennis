"""
Gal Haham
Main camera UI for capturing photos and recording videos with audio.
Handles camera preview, recording controls, FFmpeg merging,
and story upload workflow.
REFACTORED: init_ui method split into focused helper methods.
"""
import wx
import cv2
import os
import subprocess
import sys
import time

from InitCameraThread import InitCameraThread
from CameraReaderThread import CameraReaderThread
from UploadThread import UploadThread
from Audio_Recorder import AudioRecorder

SECONDS_IN_MINUTE = 60
HALF = 2
CHANNELS_INDEX = 2
TOP_LEFT_Y = 0
TOP_LEFT_X = 0
EXIT_CODE_SUCCESS = 0
TIMER_INTERVAL_MS = 33
MIN_REQUIRED_ARGS_COUNT = 2
USERNAME_ARG_INDEX = 1
SECOND_ARG_INDEX = 2


class StoryCameraFrame(wx.Frame):
    """
    Main wxPython UI window for capturing and posting stories (photo or video).

    Responsibilities:
    - Initialize and manage the camera preview.
    - Handle photo capture and video recording with audio.
    - Switch between live camera mode and preview mode.
    - Manage FFmpeg merging, UI events, painting, and rendering.
    - Interact with background worker threads (CameraReaderThread,
    InitCameraThread).
    - Dispatch the upload using UploadThread and handle success/failure UI.

    REFACTORED: Large methods split into focused helper
    methods for better maintainability.
    """

    def __init__(self, parent, username, on_post_callback, closed_callback):
        """
        Initialize the story camera frame.

        Args:
            parent: Parent window (can be None)
            username: Current user's username
            on_post_callback: Callback function when story is posted
            closed_callback: Callback function when window is closed
        """
        super().__init__(
            parent,
            title="Create Story",
            size=wx.Size(480, 750),
            style=(
                wx.DEFAULT_FRAME_STYLE & ~
                (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
            )
        )

        # Store callbacks
        self.username = username
        self.on_post_callback = on_post_callback
        self.closed_callback = closed_callback

        # Initialize state variables
        self._initialize_camera_state()
        self._initialize_recording_state()
        self._initialize_audio_state()

        # Build UI and start camera
        self.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.init_ui()
        self.Centre()
        self.Show()
        InitCameraThread(self)

    def _initialize_camera_state(self):
        """Initialize camera-related state variables."""
        self.camera = None
        self.camera_reader_thread = None
        self.is_capturing = False
        self._current_frame_cache = None
        self.mode = 'photo'
        self.captured_photo = None
        self.preview_image = None

    def _initialize_recording_state(self):
        """Initialize video recording state variables."""
        self.is_recording = False
        self.video_writer = None
        self.temp_video_path = None
        self.recording_start_time = None
        self.max_video_duration = 15
        self.preview_mode = False
        self.preview_type = None
        self.capture_enabled = False
        self.button_expanded = False
        self.button_size = 70

    def _initialize_audio_state(self):
        """Initialize audio recording state variables."""
        self.audio_recorder = None
        self.audio_path = os.path.join(os.getcwd(), "story_audio.wav")
        self.final_video_path = None

    def init_ui(self):
        """
        Build the camera window UI - REFACTORED.

        Creates all UI components using helper methods for better organization.
        """
        main_panel = self._create_main_panel()

        self._add_header(main_panel)
        self._add_camera_panel(main_panel)
        self._add_recording_indicator()
        self._add_mode_selector(main_panel)
        self._add_capture_button(main_panel)
        self._add_preview_panel(main_panel)

        self._finalize_ui_setup(main_panel)

    def _create_main_panel(self):
        """Create and configure the main panel."""
        main_panel = wx.Panel(self)
        main_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        return main_panel

    def _add_header(self, main_panel):
        """Add header panel with close button and title."""
        header_panel = wx.Panel(main_panel)
        header_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Close button
        close_btn = self._create_close_button(header_panel)
        header_sizer.Add(close_btn, 0, wx.ALL, 10)
        header_sizer.AddStretchSpacer()

        # Title text
        self.title_text = self._create_title_text(header_panel)
        header_sizer.Add(
            self.title_text,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            10
        )
        header_sizer.AddStretchSpacer()
        header_sizer.AddSpacer(50)

        header_panel.SetSizer(header_sizer)
        self.main_sizer.Add(header_panel, 0, wx.EXPAND)

    def _create_close_button(self, parent):
        """Create and configure the close button."""
        close_btn = wx.Button(
            parent,
            label="X",
            size=(40, 40),
            style=wx.BORDER_NONE
        )
        close_btn.SetBackgroundColour(wx.Colour(50, 50, 50))
        close_btn.SetForegroundColour(wx.WHITE)
        close_btn.SetFont(
            wx.Font(
                16,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        return close_btn

    def _create_title_text(self, parent):
        """Create and configure the title text widget."""
        title_text = wx.StaticText(
            parent,
            label="Initializing Camera..."
        )
        title_text.SetForegroundColour(wx.WHITE)
        title_text.SetFont(
            wx.Font(
                14,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        return title_text

    def _add_camera_panel(self, main_panel):
        """Add camera preview panel with loading indicator."""
        self.camera_panel = wx.Panel(main_panel, size=(-1, 500))
        self.camera_panel.SetBackgroundColour(wx.Colour(30, 30, 30))
        self.main_sizer.Add(self.camera_panel, 1, wx.EXPAND | wx.ALL, 0)

        # Loading text
        self.loading_text = wx.StaticText(
            self.camera_panel,
            label=" Loading Camera...",
            pos=(150, 230)
        )
        self.loading_text.SetForegroundColour(wx.Colour(200, 200, 200))
        self.loading_text.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL
            )
        )

    def _add_recording_indicator(self):
        """Add recording indicator overlay to camera panel."""
        self.recording_indicator = wx.Panel(
            self.camera_panel,
            pos=(10, 10),
            size=(120, 35)
        )
        self.recording_indicator.SetBackgroundColour(wx.Colour(220, 50, 50))

        rec_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Recording dot
        rec_dot = wx.StaticText(self.recording_indicator, label="O")
        rec_dot.SetForegroundColour(wx.WHITE)
        rec_dot.SetFont(
            wx.Font(
                16,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        rec_sizer.Add(rec_dot, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)

        # Recording timer
        self.recording_timer = wx.StaticText(
            self.recording_indicator,
            label="0:00"
        )
        self.recording_timer.SetForegroundColour(wx.WHITE)
        self.recording_timer.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        rec_sizer.Add(
            self.recording_timer,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
            5
        )

        self.recording_indicator.SetSizer(rec_sizer)
        self.recording_indicator.Hide()

    def _add_mode_selector(self, main_panel):
        """Add photo/video mode selector panel."""
        mode_panel = wx.Panel(main_panel)
        mode_panel.SetBackgroundColour(wx.Colour(15, 15, 15))
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mode_sizer.AddStretchSpacer()

        # Photo button
        self.photo_btn = self._create_photo_button(mode_panel)
        mode_sizer.Add(self.photo_btn, 0, wx.ALL, 5)

        # Video button
        self.video_btn = self._create_video_button(mode_panel)
        mode_sizer.Add(self.video_btn, 0, wx.ALL, 5)

        mode_sizer.AddStretchSpacer()
        mode_panel.SetSizer(mode_sizer)
        self.main_sizer.Add(mode_panel, 0, wx.EXPAND)

    def _create_photo_button(self, parent):
        """Create and configure the photo mode button."""
        photo_btn = wx.Button(
            parent,
            label="PHOTO",
            size=(100, 35),
            style=wx.BORDER_NONE
        )
        photo_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        photo_btn.SetForegroundColour(wx.Colour(0, 0, 0))
        photo_btn.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        photo_btn.Bind(wx.EVT_BUTTON, lambda e: self.switch_mode('photo'))
        return photo_btn

    def _create_video_button(self, parent):
        """Create and configure the video mode button."""
        video_btn = wx.Button(
            parent,
            label="VIDEO",
            size=(100, 35),
            style=wx.BORDER_NONE
        )
        video_btn.SetBackgroundColour(wx.Colour(50, 50, 50))
        video_btn.SetForegroundColour(wx.Colour(150, 150, 150))
        video_btn.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        video_btn.Bind(wx.EVT_BUTTON, lambda e: self.switch_mode('video'))
        return video_btn

    def _add_capture_button(self, main_panel):
        """Add the circular capture button panel."""
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

    def _add_preview_panel(self, main_panel):
        """Add preview panel with action buttons."""
        self.preview_panel = wx.Panel(main_panel)
        self.preview_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        preview_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Watch video button
        self.watch_video_btn = self._create_watch_video_button()
        preview_sizer.Add(self.watch_video_btn, 0, wx.ALL, 10)

        # Retake button
        retake_btn = self._create_retake_button()
        preview_sizer.Add(retake_btn, 0, wx.ALL, 10)

        # Post button
        post_btn = self._create_post_button()
        preview_sizer.Add(post_btn, 0, wx.ALL, 10)

        preview_sizer.AddStretchSpacer()
        self.preview_panel.SetSizer(preview_sizer)
        self.preview_panel.Hide()
        self.main_sizer.Add(self.preview_panel, 0, wx.EXPAND | wx.ALL, 5)

    def _create_watch_video_button(self):
        """Create the watch video button."""
        btn = wx.Button(
            self.preview_panel,
            label="Watch Video",
            size=(120, 45)
        )
        btn.SetBackgroundColour(wx.Colour(0, 120, 215))
        btn.SetForegroundColour(wx.WHITE)
        btn.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        btn.Bind(wx.EVT_BUTTON, self.on_watch_video)
        return btn

    def _create_retake_button(self):
        """Create the retake button."""
        btn = wx.Button(
            self.preview_panel,
            label="Retake",
            size=(120, 45)
        )
        btn.SetBackgroundColour(wx.Colour(50, 50, 50))
        btn.SetForegroundColour(wx.WHITE)
        btn.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        btn.Bind(wx.EVT_BUTTON, self.on_retake)
        return btn

    def _create_post_button(self):
        """Create the post story button."""
        btn = wx.Button(
            self.preview_panel,
            label="Post Story",
            size=(120, 45)
        )
        btn.SetBackgroundColour(wx.Colour(76, 175, 80))
        btn.SetForegroundColour(wx.WHITE)
        btn.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        btn.Bind(wx.EVT_BUTTON, self.on_post)
        return btn

    def _finalize_ui_setup(self, main_panel):
        """Finalize UI setup with event bindings and timers."""
        main_panel.SetSizer(self.main_sizer)
        self.camera_panel.Bind(wx.EVT_PAINT, self.on_paint)

        # Setup update timer
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_frame, self.timer)
        self.timer.Start(TIMER_INTERVAL_MS)

    def on_camera_ready(self, camera):
        """
        Called by InitCameraThread when camera successfully opens.

        Args:
            camera: Initialized cv2.VideoCapture object
        """
        print("[DEBUG on_camera_ready] Camera initialized")
        self.camera = camera
        self.is_capturing = True
        self.camera_reader_thread = CameraReaderThread(self.camera)
        self.title_text.SetLabel("Take Photo")
        self.loading_text.Hide()
        self.capture_enabled = True

        # Force UI refresh
        self.camera_panel.Refresh()
        self.camera_panel.Update()
        self.Refresh()
        self.Update()

        print("[DEBUG on_camera_ready] Camera ready!")

    def on_camera_fail(self):
        """Called by InitCameraThread on camera initialization failure."""
        self.is_capturing = False
        self.title_text.SetLabel("Camera Error")
        self.loading_text.SetLabel(" Failed to open camera")
        wx.MessageBox(
            "Failed to open camera. Check if camera is in use.",
            "Error",
            wx.OK | wx.ICON_ERROR
        )
        self.on_close(None)

    def update_frame(self, event):
        """
        Timer callback for camera preview and recording updates.

        Responsibilities:
        - Pull latest frame from CameraReaderThread
        - Write frames to video_writer if recording
        - Update recording timer
        - Trigger UI refresh

        Args:
            event: wx.TimerEvent
        """
        if (
                not self.preview_mode and
                self.is_capturing and
                self.camera_reader_thread
        ):
            frame = self.camera_reader_thread.get_frame()
            if frame is not None:
                self._current_frame_cache = frame

                if self.is_recording and self.video_writer:
                    self._update_recording_frame(frame)

                self.camera_panel.Refresh()

    def _update_recording_frame(self, frame):
        """
        Update recording with current frame and timer.

        Args:
            frame: Current video frame to write
        """
        self.video_writer.write(frame)
        elapsed = time.time() - self.recording_start_time
        mins = int(elapsed // SECONDS_IN_MINUTE)
        secs = int(elapsed % SECONDS_IN_MINUTE)
        self.recording_timer.SetLabel(f"{mins}: {secs: 02d}")

        if elapsed >= self.max_video_duration:
            self.stop_recording()

    def on_paint(self, event):
        """
        Draw camera preview or captured image.

        Args:
            event: wx.PaintEvent
        """
        dc = wx.PaintDC(self.camera_panel)

        if self.preview_mode and self.preview_image:
            dc.DrawBitmap(self.preview_image, TOP_LEFT_X, TOP_LEFT_Y)
        elif self._current_frame_cache is not None:
            self._draw_camera_frame(dc)

    def _draw_camera_frame(self, dc):
        """
        Draw the current camera frame to the device context.

        Args:
            dc: wx.DeviceContext to draw on
        """
        frame = cv2.cvtColor(self._current_frame_cache, cv2.COLOR_BGR2RGB)
        h, w = frame.shape[:CHANNELS_INDEX]
        panel_size = self.camera_panel.GetSize()
        scale = min(panel_size.width / w, panel_size.height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h))
        image = wx.Image(new_w, new_h, frame.tobytes())
        bitmap = wx.Bitmap(image)
        x = (panel_size.width - new_w) // HALF
        y = (panel_size.height - new_h) // HALF
        dc.Clear()
        dc.DrawBitmap(bitmap, x, y)

    def on_paint_button(self, event):
        """
        Draw the circular capture button.

        Args:
            event: wx.PaintEvent
        """
        dc = wx.PaintDC(self.button_container)
        gc = wx.GraphicsContext.Create(dc)
        if gc:
            gc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
            gc.DrawRectangle(0, 0, 100, 100)
            center_x, center_y = 50, 50
            outer_size = self.button_size
            gc.SetBrush(wx.Brush(wx.Colour(255, 255, 255)))
            gc.DrawEllipse(
                center_x - outer_size / 2,
                center_y - outer_size / 2,
                outer_size,
                outer_size
            )
            inner_size = outer_size * 0.7
            gc.SetBrush(wx.Brush(wx.Colour(255, 50, 80)))
            gc.DrawEllipse(
                center_x - inner_size / 2,
                center_y - inner_size / 2,
                inner_size,
                inner_size
            )

    def on_button_click(self, event):
        """
        Handle capture button click.

        Behavior depends on current mode:
        - Photo mode: Capture photo immediately
        - Video mode: Start/stop recording

        Args:
            event: wx.MouseEvent
        """
        if not self.capture_enabled or not self.is_capturing:
            return

        if self.mode == 'photo':
            self.capture_photo()
        elif self.mode == 'video':
            self._handle_video_button_click()

    def _handle_video_button_click(self):
        """Handle video mode button click (start/stop recording)."""
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
        Switch between photo and video capture modes.

        Args:
            mode: 'photo' or 'video'
        """
        self.mode = mode

        if mode == 'photo':
            self._activate_photo_mode()
        else:
            self._activate_video_mode()

    def _activate_photo_mode(self):
        """Activate photo capture mode UI."""
        self.photo_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.photo_btn.SetForegroundColour(wx.Colour(0, 0, 0))
        self.video_btn.SetBackgroundColour(wx.Colour(50, 50, 50))
        self.video_btn.SetForegroundColour(wx.Colour(150, 150, 150))
        self.title_text.SetLabel("Take Photo")

    def _activate_video_mode(self):
        """Activate video capture mode UI."""
        self.video_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.video_btn.SetForegroundColour(wx.Colour(0, 0, 0))
        self.photo_btn.SetBackgroundColour(wx.Colour(50, 50, 50))
        self.photo_btn.SetForegroundColour(wx.Colour(150, 150, 150))
        self.title_text.SetLabel("Record Video (Click to Start/Stop)")

    def capture_photo(self):
        """
        Capture the current camera frame as a photo.

        Converts frame to RGB, resizes for display, and enters preview mode.
        """
        if self._current_frame_cache is None:
            return

        self.captured_photo = self._current_frame_cache.copy()
        self.preview_image = self._create_preview_bitmap(self.captured_photo)
        self.preview_type = 'photo'
        self.enter_preview_mode()

    def _create_preview_bitmap(self, frame):
        """
        Create a wx.Bitmap for preview from a frame.

        Args:
            frame: OpenCV frame (BGR format)

        Returns:
            wx.Bitmap: Bitmap ready for display
        """
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame.shape[:CHANNELS_INDEX]
        panel_size = self.camera_panel.GetSize()
        scale = min(panel_size.width / w, panel_size.height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h))
        return wx.Bitmap(wx.Image(new_w, new_h, frame.tobytes()))

    def start_recording(self):
        """
        Start video and audio recording.

        Initializes:
        - Video writer (OpenCV)
        - Audio recorder (PyAudio)
        - Recording timer UI
        """
        if self._current_frame_cache is None or self.is_recording:
            return

        self.temp_video_path = os.path.join(os.getcwd(), "story_raw.mp4")

        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        h, w = self._current_frame_cache.shape[:CHANNELS_INDEX]
        self.video_writer = cv2.VideoWriter(
            self.temp_video_path,
            fourcc,
            20.0,
            (w, h)
        )

        # Initialize audio recorder
        self.audio_recorder = AudioRecorder()
        self.audio_recorder.start_recording()

        # Start recording
        self.is_recording = True
        self.recording_start_time = time.time()
        self.recording_indicator.Show()

    def stop_recording(self):
        """
        Stop video and audio recording.

        Performs:
        - Stops and releases video writer
        - Stops and saves audio
        - Merges video and audio with FFmpeg
        - Enters preview mode
        """
        if not self.is_recording:
            return

        self.is_recording = False
        self.recording_indicator.Hide()

        # Stop video writer
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        # Stop and save audio
        if self.audio_recorder:
            self.audio_recorder.stop_recording()
            self.audio_recorder.save_audio(self.audio_path)
            self.audio_recorder.cleanup()
            self.audio_recorder = None

        # Create preview thumbnail
        self._create_video_preview_thumbnail()

        # Merge audio and video
        self.final_video_path = os.path.join(os.getcwd(), "story_final.mp4")
        merged_path = self.merge_audio_video(
            self.temp_video_path,
            self.audio_path,
            self.final_video_path
        )

        if merged_path is None:
            self.final_video_path = self.temp_video_path

        self.preview_type = 'video'
        self.enter_preview_mode()

    def _create_video_preview_thumbnail(self):
        """Extract first frame of recorded video for preview."""
        frame_cap = cv2.VideoCapture(self.temp_video_path)
        ret, frame = frame_cap.read()
        frame_cap.release()

        if ret and frame is not None:
            self.preview_image = self._create_preview_bitmap(frame)

    def merge_audio_video(self, video_path, audio_path, output_path):
        """
        Merge video and audio using FFmpeg.

        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Path for merged output

        Returns:
            str: Path to merged file, or None on failure
        """
        if not os.path.exists(video_path):
            print("merge_audio_video: video file not found")
            return None

        # If no audio, just copy video
        if not os.path.exists(audio_path):
            return self._copy_video_without_audio(video_path, output_path)

        # Merge with FFmpeg
        return self._merge_with_ffmpeg(video_path, audio_path, output_path)

    def _copy_video_without_audio(self, video_path, output_path):
        """
        Copy video file when no audio is available.

        Args:
            video_path: Source video path
            output_path: Destination path

        Returns:
            str: Output path on success, None on failure
        """
        try:
            import shutil
            shutil.copy(video_path, output_path)
            return output_path
        except Exception as e:
            print(f"Failed to copy video without audio: {e}")
            return None

    def _merge_with_ffmpeg(self, video_path, audio_path, output_path):
        """
        Merge video and audio files using FFmpeg.

        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Path for output file

        Returns:
            str: Output path on success, None on failure
        """
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
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode != EXIT_CODE_SUCCESS:
                print("ffmpeg error:", result.stderr.decode(errors='ignore'))
                return None
            return output_path
        except Exception as e:
            print("merge_audio_video: exception while running ffmpeg:", e)
            return None

    def enter_preview_mode(self):
        """Switch UI to preview mode."""
        self.preview_mode = True
        self.camera_panel.Hide()
        self.preview_panel.Show()
        self.main_sizer.Layout()

    def exit_preview_mode(self):
        """Return to live camera mode."""
        self.preview_mode = False
        self.camera_panel.Show()
        self.preview_panel.Hide()
        self.preview_image = None
        self.preview_type = None
        self.main_sizer.Layout()
        self.camera_panel.Refresh()

    def on_retake(self, event):
        """
        Handle retake button - return to camera mode.

        Args:
            event: wx.Event
        """
        self.exit_preview_mode()

    def on_watch_video(self, event):
        """
        Open recorded video in default media player.

        Args:
            event: wx.Event
        """
        if self.preview_type != 'video':
            return

        path_to_open = (
            self.final_video_path
            if self.final_video_path and os.path.exists(self.final_video_path)
            else self.temp_video_path
        )

        if not path_to_open or not os.path.exists(path_to_open):
            return

        self._open_file_with_default_app(path_to_open)

    def _open_file_with_default_app(self, file_path):
        """
        Open file with system default application.

        Args:
            file_path: Path to file to open
        """
        if sys.platform.startswith('win'):
            os.startfile(file_path)
        elif sys.platform.startswith('darwin'):
            subprocess.call(('open', file_path))
        else:
            subprocess.call(('xdg-open', file_path))

    def on_post(self, event):
        """
        Post the captured story (photo or video).

        Args:
            event: wx.Event
        """
        if self.preview_type == 'photo' and self.captured_photo is not None:
            self._post_photo()
        elif self.preview_type == 'video' and self.final_video_path:
            self._post_video()
        else:
            wx.MessageBox("No media to post.", "Error", wx.OK | wx.ICON_ERROR)

    def _post_photo(self):
        """Post captured photo using UploadThread."""
        UploadThread(
            self.captured_photo,
            None,
            "",
            'photo',
            self.on_post_callback,
            self
        )

    def _post_video(self):
        """Post recorded video using UploadThread."""
        UploadThread(
            None,
            self.final_video_path,
            "",
            'video',
            self.on_post_callback,
            self
        )

    def post_successful(self, media_type):
        """
        Called by UploadThread after successful upload.

        Args:
            media_type: 'photo' or 'video'
        """
        wx.MessageBox(
            f"{media_type.capitalize()} posted successfully!",
            "Success",
            wx.OK | wx.ICON_INFORMATION
        )
        self.on_retake(None)

    def post_failed(self, message):
        """
        Called by UploadThread on upload failure.

        Args:
            message: Error message to display
        """
        wx.MessageBox(
            f"Failed to post: {message}",
            "Error",
            wx.OK | wx.ICON_ERROR
        )

    def on_close(self, event):
        """
        Clean up resources and close window.

        Args:
            event: wx.Event (can be None)
        """
        # Stop camera threads
        if self.camera_reader_thread:
            self.camera_reader_thread.stop()
        if self.camera and self.camera.isOpened():
            self.camera.release()

        # Call the callback BEFORE destroying
        if self.closed_callback:
            self.closed_callback()

        # Now destroy the window
        self.Destroy()


if __name__ == '__main__':
    """Test harness for standalone execution."""
    if len(sys.argv) >= MIN_REQUIRED_ARGS_COUNT:
        username = sys.argv[USERNAME_ARG_INDEX]
        callback_file = (
            sys.argv[SECOND_ARG_INDEX]
            if len(sys.argv) > SECOND_ARG_INDEX
            else None
        )

        def on_post_subprocess(caption, media_type, media_data):
            """Handle story post in subprocess mode."""
            if callback_file:
                import pickle
                data = {
                    'posted': True,
                    'caption': caption,
                    'media_type': media_type,
                    'media_data': media_data
                }
                with open(callback_file, 'wb') as f:
                    pickle.dump(data, f)

        def on_closed_subprocess():
            """Handle window close in subprocess mode."""
            print("[DEBUG subprocess] Camera closed")

        app = wx.App()
        frame = StoryCameraFrame(None,
                                 username,
                                 on_post_subprocess,
                                 on_closed_subprocess)
        app.MainLoop()
    else:
        # Test mode
        def test_callback(caption, media_type, media_data):
            """Test callback for development."""
            print(f"Callback received data.")
            print(f"Caption: {caption}")
            print(f"Media Type: {media_type}")
            print(f"Media Data Length: {len(media_data)} characters")

        def closed_callback():
            """Test close callback."""
            print("Camera frame closed")

        app = wx.App()
        frame = StoryCameraFrame(None,
                                 "test_user",
                                 test_callback,
                                 closed_callback)
        app.MainLoop()
