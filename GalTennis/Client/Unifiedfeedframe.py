"""
Gal Haham
Unified Feed Frame - Main application window with tabs
Combines Stories and Videos in one clean interface
"""
import wx
import socket
import json
import base64
import io
import time
from Story_camera import StoryCameraFrame
from VideoInteractionFrame import VideoInteractionFrame
from UploadVideoFrame import UploadVideoFrame
from Video_Player_Client import run_video_player_client
from story_player_client import run_story_player_client

# Window Configuration
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
WINDOW_TITLE = "Tennis Social"

# Colors
COLOR_HEADER_BG = wx.Colour(40, 120, 80)  # Green tennis
COLOR_TAB_ACTIVE = wx.Colour(76, 175, 80)  # Active tab
COLOR_TAB_INACTIVE = wx.Colour(200, 200, 200)  # Inactive tab
COLOR_BACKGROUND = wx.Colour(245, 245, 245)  # Light gray
COLOR_WHITE = wx.WHITE
COLOR_TEXT_DARK = wx.Colour(50, 50, 50)

# Grid
GRID_COLUMNS = 3
GRID_GAP = 15
THUMBNAIL_SIZE = 200

# Server Configuration
SERVER_IP = '127.0.0.1'
STORY_THUMBNAIL_PORT = 2222
VIDEO_THUMBNAIL_PORT = 2223
RECV_BUFFER_SIZE = 4096

# Timing
SERVER_START_DELAY = 1


class UnifiedFeedFrame(wx.Frame):
    """
    Main application window with tabbed interface.

    Features:
    - Stories tab with grid of story thumbnails
    - Videos tab with grid of video thumbnails
    - Header with notifications and settings
    """

    def __init__(self, client, username):
        """Initialize the unified feed frame."""
        super().__init__(
            None,
            title=WINDOW_TITLE,
            size=(WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        self.client = client
        self.username = username
        self.current_tab = "videos"  # Start with videos

        # Initialize data
        self.stories_data = []
        self.videos_data = []

        # Build UI
        self._init_ui()

        self.Centre()
        self.Show()

        # Auto-load videos on startup
        wx.CallAfter(self.show_videos_tab)

    def _init_ui(self):
        """Initialize the user interface."""
        # Main panel
        self.main_panel = wx.Panel(self)
        self.main_panel.SetBackgroundColour(COLOR_BACKGROUND)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header = self._create_header()
        main_sizer.Add(header, 0, wx.EXPAND)

        # Tab buttons
        tab_bar = self._create_tab_bar()
        main_sizer.Add(tab_bar, 0, wx.EXPAND)

        # Content area (scrollable)
        self.content_scroll = wx.ScrolledWindow(
            self.main_panel,
            style=wx.VSCROLL
        )
        self.content_scroll.SetScrollRate(0, 20)
        self.content_scroll.SetBackgroundColour(COLOR_BACKGROUND)

        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.content_scroll.SetSizer(self.content_sizer)

        main_sizer.Add(self.content_scroll, 1, wx.EXPAND)

        self.main_panel.SetSizer(main_sizer)

    def _create_header(self):
        """Create the header with logo and user info."""
        header_panel = wx.Panel(self.main_panel)
        header_panel.SetBackgroundColour(COLOR_HEADER_BG)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Logo/Title
        title = wx.StaticText(header_panel, label="Tennis Social")
        title.SetForegroundColour(COLOR_WHITE)
        title_font = wx.Font(
            18,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title.SetFont(title_font)
        header_sizer.Add(title, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 15)

        header_sizer.AddStretchSpacer(1)

        # User info
        user_text = wx.StaticText(header_panel, label=f"{self.username}")
        user_text.SetForegroundColour(COLOR_WHITE)
        user_font = wx.Font(
            12,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        user_text.SetFont(user_font)
        header_sizer.Add(user_text, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 15)

        # Logout button
        logout_btn = wx.Button(header_panel, label="Logout", size=(80, 30))
        logout_btn.SetBackgroundColour(wx.Colour(220, 53, 69))
        logout_btn.SetForegroundColour(COLOR_WHITE)
        logout_btn.Bind(wx.EVT_BUTTON, self.on_logout)
        header_sizer.Add(logout_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)

        header_panel.SetSizer(header_sizer)
        return header_panel

    def _create_tab_bar(self):
        """Create the tab navigation bar."""
        tab_panel = wx.Panel(self.main_panel)
        tab_panel.SetBackgroundColour(COLOR_WHITE)
        tab_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Stories tab
        self.stories_btn = wx.Button(
            tab_panel,
            label="Stories",
            size=(200, 50)
        )
        self.stories_btn.SetBackgroundColour(COLOR_TAB_INACTIVE)
        self.stories_btn.Bind(wx.EVT_BUTTON, lambda e: self.show_stories_tab())
        tab_sizer.Add(self.stories_btn, 0, wx.ALL, 5)

        # Videos tab
        self.videos_btn = wx.Button(
            tab_panel,
            label="Videos",
            size=(200, 50)
        )
        self.videos_btn.SetBackgroundColour(COLOR_TAB_ACTIVE)
        self.videos_btn.Bind(wx.EVT_BUTTON, lambda e: self.show_videos_tab())
        tab_sizer.Add(self.videos_btn, 0, wx.ALL, 5)

        tab_panel.SetSizer(tab_sizer)
        return tab_panel

    def _update_tab_colors(self):
        """Update tab button colors based on active tab."""
        if self.current_tab == "stories":
            self.stories_btn.SetBackgroundColour(COLOR_TAB_ACTIVE)
            self.videos_btn.SetBackgroundColour(COLOR_TAB_INACTIVE)
        elif self.current_tab == "videos":
            self.stories_btn.SetBackgroundColour(COLOR_TAB_INACTIVE)
            self.videos_btn.SetBackgroundColour(COLOR_TAB_ACTIVE)
            self.stories_btn.SetBackgroundColour(COLOR_TAB_INACTIVE)
            self.videos_btn.SetBackgroundColour(COLOR_TAB_INACTIVE)

        self.stories_btn.Refresh()
        self.videos_btn.Refresh()

    def show_stories_tab(self):
        """Show stories tab with grid of thumbnails."""
        self.current_tab = "stories"
        self._update_tab_colors()

        # Clear content
        self.content_sizer.Clear(True)

        # Header with Post button
        header_panel = wx.Panel(self.content_scroll)
        header_panel.SetBackgroundColour(COLOR_BACKGROUND)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        title = wx.StaticText(header_panel, label="Stories")
        title_font = wx.Font(
            16,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title.SetFont(title_font)
        title.SetForegroundColour(COLOR_TEXT_DARK)
        header_sizer.Add(title, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 15)

        header_sizer.AddStretchSpacer(1)

        # Post Story button
        post_btn = wx.Button(
            header_panel,
            label="+ Post Story",
            size=(150, 40)
        )
        post_btn.SetBackgroundColour(COLOR_TAB_ACTIVE)
        post_btn.SetForegroundColour(COLOR_WHITE)
        post_btn.Bind(wx.EVT_BUTTON, self.on_post_story)
        header_sizer.Add(post_btn, 0, wx.ALL, 10)

        header_panel.SetSizer(header_sizer)
        self.content_sizer.Add(header_panel, 0, wx.EXPAND)

        # Load and display stories
        self._load_and_display_stories()

    def _load_and_display_stories(self):
        """Load stories from server and display in grid."""
        try:
            # Request server to start thumbnail server
            response = self.client._send_request(
                'GET_IMAGES_OF_ALL_VIDEOS',
                {}
            )
            time.sleep(SERVER_START_DELAY)

            # Fetch stories
            self.stories_data = self._fetch_stories_from_server()

            if not self.stories_data:
                no_stories = wx.StaticText(
                    self.content_scroll,
                    label="No stories yet. Post your first story!"
                )
                no_stories.SetForegroundColour(wx.Colour(150, 150, 150))
                self.content_sizer.Add(
                    no_stories,
                    0,
                    wx.ALL | wx.ALIGN_CENTER,
                    50
                )
            else:
                # Create grid
                grid_panel = wx.Panel(self.content_scroll)
                grid_panel.SetBackgroundColour(COLOR_BACKGROUND)
                grid_sizer = wx.GridSizer(
                    cols=GRID_COLUMNS,
                    hgap=GRID_GAP,
                    vgap=GRID_GAP
                )

                for story in self.stories_data:
                    story_card = self._create_story_card(grid_panel, story)
                    grid_sizer.Add(story_card, 0, wx.EXPAND)

                grid_panel.SetSizer(grid_sizer)
                self.content_sizer.Add(
                    grid_panel,
                    0,
                    wx.ALL | wx.ALIGN_CENTER,
                    20
                )

        except Exception as e:
            error_msg = wx.StaticText(
                self.content_scroll,
                label=f"Error loading stories: {str(e)}"
            )
            error_msg.SetForegroundColour(wx.Colour(200, 0, 0))
            self.content_sizer.Add(error_msg, 0, wx.ALL | wx.ALIGN_CENTER, 50)

        self.content_scroll.Layout()
        self.content_scroll.FitInside()

    def _fetch_stories_from_server(self):
        """Fetch stories from thumbnail server."""
        response = self.client._send_request(
            'GET_MEDIA',
            {}
        )
        print("_fetch_stories_from_server")
        print(response.get('payload'))
        #return json.loads(response.get('payload'))
        return response.get('payload')


    def _create_story_card(self, parent, story):
        """Create a story thumbnail card."""
        card = wx.Panel(parent, size=(THUMBNAIL_SIZE, THUMBNAIL_SIZE + 60))
        card.SetBackgroundColour(COLOR_WHITE)
        card_sizer = wx.BoxSizer(wx.VERTICAL)

        # Thumbnail
        img_data = base64.b64decode(story['thumbnail'])
        img_stream = io.BytesIO(img_data)
        img = wx.Image(img_stream)
        img = img.Scale(THUMBNAIL_SIZE, THUMBNAIL_SIZE, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(img)

        img_ctrl = wx.StaticBitmap(card, bitmap=bitmap)
        img_ctrl.Bind(
            wx.EVT_LEFT_DCLICK,
            lambda e: self.on_story_click(story)
        )
        img_ctrl.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        card_sizer.Add(img_ctrl, 0, wx.ALL | wx.CENTER, 0)

        # Info
        name_label = wx.StaticText(card, label=story['name'][:20])
        name_label.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        card_sizer.Add(name_label, 0, wx.ALL | wx.CENTER, 5)

        card.SetSizer(card_sizer)
        return card

    def on_story_click(self, story):
        """Handle story click - play story."""
        story_name = story['name']
        print(f"Playing story: {story_name}")

        try:
            response = self.client._send_request('PLAY_STORY', {
                'filename': story_name
            })

            if response.get('status') == 'success':
                time.sleep(2)
                run_story_player_client()
        except Exception as e:
            wx.MessageBox(
                f"Error playing story: {str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )

    def on_post_story(self, event):
        """Open camera to post new story."""

        def on_post_callback(caption, media_type, media_data):
            self.client.on_story_post_callback(caption, media_type, media_data)

        def on_closed_callback():
            print("Camera closed")

        StoryCameraFrame(
            None,
            self.username,
            on_post_callback,
            on_closed_callback
        )

    def show_videos_tab(self):
        """Show videos tab with grid of thumbnails."""
        self.current_tab = "videos"
        self._update_tab_colors()

        # Clear content
        self.content_sizer.Clear(True)

        # Header with Upload button
        header_panel = wx.Panel(self.content_scroll)
        header_panel.SetBackgroundColour(COLOR_BACKGROUND)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        title = wx.StaticText(header_panel, label="Videos")
        title_font = wx.Font(
            16,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title.SetFont(title_font)
        title.SetForegroundColour(COLOR_TEXT_DARK)
        header_sizer.Add(title, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 15)

        header_sizer.AddStretchSpacer(1)

        # Upload Video button
        upload_btn = wx.Button(header_panel, label="+ Upload", size=(150, 40))
        upload_btn.SetBackgroundColour(COLOR_TAB_ACTIVE)
        upload_btn.SetForegroundColour(COLOR_WHITE)
        upload_btn.Bind(wx.EVT_BUTTON, self.on_upload_video)
        header_sizer.Add(upload_btn, 0, wx.ALL, 10)

        header_panel.SetSizer(header_sizer)
        self.content_sizer.Add(header_panel, 0, wx.EXPAND)

        # Load and display videos
        self._load_and_display_videos()

    def _load_and_display_videos(self):
        """Load videos from server and display in grid."""
        try:
            # Request server to start thumbnail server
            response = self.client._send_request('GET_ALL_VIDEOS_GRID', {})
            time.sleep(SERVER_START_DELAY)

            # Fetch videos
            self.videos_data = self._fetch_videos_from_server()

            if not self.videos_data:
                no_videos = wx.StaticText(
                    self.content_scroll,
                    label="No videos yet. Upload your first video!"
                )
                no_videos.SetForegroundColour(wx.Colour(150, 150, 150))
                self.content_sizer.Add(
                    no_videos,
                    0,
                    wx.ALL | wx.ALIGN_CENTER,
                    50
                )
            else:
                # Create grid
                grid_panel = wx.Panel(self.content_scroll)
                grid_panel.SetBackgroundColour(COLOR_BACKGROUND)
                grid_sizer = wx.GridSizer(
                    cols=GRID_COLUMNS,
                    hgap=GRID_GAP,
                    vgap=GRID_GAP
                )

                for video in self.videos_data:
                    video_card = self._create_video_card(grid_panel, video)
                    grid_sizer.Add(video_card, 0, wx.EXPAND)

                grid_panel.SetSizer(grid_sizer)
                self.content_sizer.Add(
                    grid_panel,
                    0,
                    wx.ALL | wx.ALIGN_CENTER,
                    20
                )

        except Exception as e:
            error_msg = wx.StaticText(
                self.content_scroll,
                label=f"Error loading videos: {str(e)}"
            )
            error_msg.SetForegroundColour(wx.Colour(200, 0, 0))
            self.content_sizer.Add(error_msg, 0, wx.ALL | wx.ALIGN_CENTER, 50)

        self.content_scroll.Layout()
        self.content_scroll.FitInside()

    def _fetch_videos_from_server(self):
        """Fetch videos from thumbnail server."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, VIDEO_THUMBNAIL_PORT))
        sock.sendall("GET_VIDEOS_MEDIA".encode('utf-8'))

        response = b""
        while True:
            chunk = sock.recv(RECV_BUFFER_SIZE)
            if not chunk:
                break
            response += chunk
        sock.close()

        return json.loads(response.decode('utf-8'))

    def _create_video_card(self, parent, video):
        """Create a video thumbnail card."""
        card = wx.Panel(parent, size=(THUMBNAIL_SIZE, THUMBNAIL_SIZE + 100))
        card.SetBackgroundColour(COLOR_WHITE)
        card_sizer = wx.BoxSizer(wx.VERTICAL)

        # Thumbnail
        img_data = base64.b64decode(video['thumbnail'])
        img_stream = io.BytesIO(img_data)
        img = wx.Image(img_stream)
        img = img.Scale(THUMBNAIL_SIZE, THUMBNAIL_SIZE, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(img)

        img_ctrl = wx.StaticBitmap(card, bitmap=bitmap)
        img_ctrl.Bind(
            wx.EVT_LEFT_DCLICK,
            lambda e: self.on_video_click(video)
        )
        img_ctrl.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        card_sizer.Add(img_ctrl, 0, wx.ALL | wx.CENTER, 0)

        # Video info
        name_label = wx.StaticText(card, label=video['name'][:20])
        name_label.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        card_sizer.Add(name_label, 0, wx.ALL | wx.CENTER, 3)

        # Category and level
        meta_text = (
            f"{video.get('category', 'N/A')} - "
            f"{video.get('level', 'N/A')}"
        )
        meta_label = wx.StaticText(card, label=meta_text)
        meta_label.SetFont(
            wx.Font(
                8,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_ITALIC,
                wx.FONTWEIGHT_NORMAL
            )
        )
        meta_label.SetForegroundColour(wx.Colour(100, 100, 100))
        card_sizer.Add(meta_label, 0, wx.ALL | wx.CENTER, 2)

        # Uploader
        uploader_label = wx.StaticText(
            card,
            label=f"@{video.get('uploader', 'unknown')}"
        )
        uploader_label.SetFont(
            wx.Font(
                8,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL
            )
        )
        uploader_label.SetForegroundColour(wx.Colour(120, 120, 120))
        card_sizer.Add(uploader_label, 0, wx.ALL | wx.CENTER, 2)

        card.SetSizer(card_sizer)
        return card

    def on_video_click(self, video):
        """Handle video click - open interaction frame."""
        video_data = {
            'title': video['name'],
            'category': video.get('category', 'N/A'),
            'level': video.get('level', 'N/A'),
            'uploader': video.get('uploader', 'Unknown'),
            'path': video['path']
        }

        print(f"Opening video: {video_data['title']}")

        # Hide this frame
        self.Hide()

        # Open interaction frame
        VideoInteractionFrame(
            self.client,
            video_data,
            parent_window=self
        )

    def on_upload_video(self, event):
        """Open upload video window."""
        UploadVideoFrame(client=self.client)

    def on_logout(self, event):
        """Handle logout - close application gracefully."""
        result = wx.MessageBox(
            "Are you sure you want to logout?",
            "Logout",
            wx.YES_NO | wx.ICON_QUESTION
        )

        if result == wx.YES:
            # Close this window
            self.Destroy()

            # Close all other windows
            for window in wx.GetTopLevelWindows():
                if window != self:
                    window.Close(True)

            # Exit the application
            wx.GetApp().ExitMainLoop()
