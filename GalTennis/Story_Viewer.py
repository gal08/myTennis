import wx
import cv2
import os
import threading
import time


class StoryViewerFrame(wx.Frame):

    def __init__(self, parent, stories_list, username):
        super().__init__(
            parent,
            title="Stories",
            size=wx.Size(400, 700),
            style=wx.DEFAULT_FRAME_STYLE & ~(
                    wx.RESIZE_BORDER | wx.MAXIMIZE_BOX
            )

        )

        self.stories = stories_list
        self.current_index = 0
        self.username = username
        self.is_playing = False
        self.video_capture = None

        self.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.Centre()

        self.init_ui()
        self.load_story(0)

    def init_ui(self):
        main_panel = wx.Panel(self)
        main_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        header_panel = wx.Panel(main_panel)
        header_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Profile picture placeholder
        profile_btn = wx.Button(
            header_panel,
            label="",
            size=(40, 40),
            style=wx.BORDER_SIMPLE
        )

        profile_btn.SetBackgroundColour(wx.Colour(80, 80, 80))
        header_sizer.Add(profile_btn, 0, wx.ALL, 10)

        # Username
        self.username_text = wx.StaticText(header_panel, label="")
        self.username_text.SetForegroundColour(wx.WHITE)
        self.username_text.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )

        header_sizer.Add(self.username_text, 0, wx.ALIGN_CENTER_VERTICAL)

        header_sizer.AddStretchSpacer()

        # Close button
        close_btn = wx.Button(
            header_panel,
            label="✕",
            size=(40, 40),
            style=wx.BORDER_NONE
        )
        close_btn.SetBackgroundColour(wx.Colour(0, 0, 0))
        close_btn.SetForegroundColour(wx.WHITE)
        close_btn.SetFont(
            wx.Font(
                18,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )

        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        header_sizer.Add(close_btn, 0, wx.ALL, 10)

        header_panel.SetSizer(header_sizer)
        main_sizer.Add(header_panel, 0, wx.EXPAND)

        # Progress bars
        self.progress_panel = wx.Panel(main_panel)
        self.progress_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.progress_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.progress_bars = []

        for i in range(len(self.stories)):
            bar = wx.Panel(self.progress_panel, size=(-1, 3))
            bar.SetBackgroundColour(wx.Colour(100, 100, 100))
            self.progress_sizer.Add(bar, 1, wx.ALL, 2)
            self.progress_bars.append(bar)

        self.progress_panel.SetSizer(self.progress_sizer)
        main_sizer.Add(self.progress_panel, 0, wx.EXPAND | wx.ALL, 10)

        # Content area (video/image display)
        self.content_panel = wx.Panel(main_panel, size=(-1, 550))
        self.content_panel.SetBackgroundColour(wx.Colour(20, 20, 20))
        main_sizer.Add(self.content_panel, 1, wx.EXPAND)

        # Navigation areas (invisible buttons for prev/next)
        nav_panel = wx.Panel(main_panel)
        nav_panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        nav_sizer = wx.BoxSizer(wx.HORIZONTAL)

        prev_area = wx.Panel(nav_panel, size=(130, 50))
        prev_area.SetBackgroundColour(wx.Colour(0, 0, 0))
        prev_area.Bind(wx.EVT_LEFT_DOWN, self.on_previous)
        nav_sizer.Add(prev_area, 1, wx.EXPAND)

        nav_sizer.AddStretchSpacer()

        next_area = wx.Panel(nav_panel, size=(130, 50))
        next_area.SetBackgroundColour(wx.Colour(0, 0, 0))
        next_area.Bind(wx.EVT_LEFT_DOWN, self.on_next)
        nav_sizer.Add(next_area, 1, wx.EXPAND)

        nav_panel.SetSizer(nav_sizer)
        main_sizer.Add(nav_panel, 0, wx.EXPAND)

        main_panel.SetSizer(main_sizer)

        # Timer for video playback
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_video_frame, self.timer)
        self.content_panel.Bind(wx.EVT_PAINT, self.on_paint)

        self.Show()

    def load_story(self, index):
        if index < 0 or index >= len(self.stories):
            self.Close()
            return

        self.current_index = index
        story = self.stories[index]

        # Update username
        self.username_text.SetLabel(story['username'])

        # Update progress bars
        for i, bar in enumerate(self.progress_bars):
            if i < index:
                bar.SetBackgroundColour(wx.Colour(255, 255, 255))
            elif i == index:
                bar.SetBackgroundColour(wx.Colour(150, 150, 150))
            else:
                bar.SetBackgroundColour(wx.Colour(100, 100, 100))

        # Stop previous video if playing
        self.stop_video()

        # Load new story content
        if story['content_type'] == 'video':
            self.play_video(story['file_path'])
        else:
            # For text or image (we'll handle text as static display)
            self.display_static_content(story)

    def play_video(self, video_path):
        if not os.path.exists(video_path):
            wx.MessageBox(
                f"Video file not found: {video_path}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )

            self.on_next(None)
            return

        self.video_capture = cv2.VideoCapture(video_path)
        if not self.video_capture.isOpened():
            wx.MessageBox(
                "Failed to open video",
                "Error",
                wx.OK | wx.ICON_ERROR
            )

            self.on_next(None)
            return

        self.is_playing = True
        self.timer.Start(33)

    def stop_video(self):
        self.is_playing = False
        self.timer.Stop()
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

    def update_video_frame(self, event):
        if not self.is_playing or not self.video_capture:
            return

        ret, frame = self.video_capture.read()
        if not ret:
            # Video ended, move to next story
            self.stop_video()
            self.on_next(None)
            return

        self.current_frame = frame
        self.content_panel.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self.content_panel)

        if hasattr(self, 'current_frame') and self.current_frame is not None:
            frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]

            panel_size = self.content_panel.GetSize()
            scale = min(panel_size.width / w, panel_size.height / h)
            new_w, new_h = int(w * scale), int(h * scale)

            frame = cv2.resize(frame, (new_w, new_h))
            image = wx.Image(new_w, new_h, frame.tobytes())
            bitmap = wx.Bitmap(image)

            x = (panel_size.width - new_w) // 2
            y = (panel_size.height - new_h) // 2

            dc.Clear()
            dc.DrawBitmap(bitmap, x, y)

    def display_static_content(self, story):
        # Clear any video
        self.current_frame = None
        self.content_panel.Refresh()

        # Display text in center
        dc = wx.ClientDC(self.content_panel)
        dc.SetBackground(wx.Brush(wx.Colour(20, 20, 20)))
        dc.Clear()
        dc.SetTextForeground(wx.WHITE)
        dc.SetFont(
            wx.Font(
                16,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL
            )
        )

        text = story.get('content', 'No content')
        text_size = dc.GetTextExtent(text)
        panel_size = self.content_panel.GetSize()

        x = (panel_size.width - text_size[0]) // 2
        y = (panel_size.height - text_size[1]) // 2

        dc.DrawText(text, x, y)

        # Auto-advance after 5 seconds for static content
        wx.CallLater(5000, lambda: self.on_next(None))

    def on_previous(self, event):
        if self.current_index > 0:
            self.load_story(self.current_index - 1)

    def on_next(self, event):
        if self.current_index < len(self.stories) - 1:
            self.load_story(self.current_index + 1)
        else:
            self.Close()

    def on_close(self, event):
        self.stop_video()
        self.Destroy()


def show_stories(parent, stories_list, username):
    if not stories_list:
        wx.MessageBox(
            "No stories available",
            "Info",
            wx.OK | wx.ICON_INFORMATION
        )

        return

    viewer = StoryViewerFrame(parent, stories_list, username)
