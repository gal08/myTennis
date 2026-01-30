"""
Gal Haham
Video grid panel for displaying video thumbnails.
Shows videos in a scrollable grid layout with metadata.
REFACTORED: Separated class, all constants added, methods split.
"""
import time
import wx
import socket
import json
import base64
import io
from Video_Player_Client import run_video_player_client
from VideoInteractionFrame import VideoInteractionFrame

# Server Configuration
SERVER_IP = '127.0.0.1'
VIDEO_THUMBNAIL_PORT = 2223

# Timing
TWO_SECOND_PAUSE = 2
SERVER_START_DELAY = 1

# Grid Display
THUMBNAIL_SIZE = 200
GRID_COLUMNS = 3
GRID_GAP = 10

# Spacing
SPACING_SCROLL = 10
SPACING_THUMBNAIL = 5
SPACING_METADATA = 2

# Scroll Configuration
SCROLL_RATE_X = 0
SCROLL_RATE_Y = 20

# Network
RECV_BUFFER_SIZE = 4096

# Colors
COLOR_PANEL_BACKGROUND = wx.Colour(240, 240, 240)

# Fonts
FONT_SIZE_TITLE = 9
FONT_SIZE_METADATA = 8


class VideoGridPanel(wx.Panel):
    """
    Panel displaying grid of video thumbnails with metadata.

    Features:
    - Load videos from server
    - Display in scrollable grid
    - Show thumbnails and metadata
    - Handle video selection

    REFACTORED: All magic numbers replaced with constants.
    """

    def __init__(self, parent, client_ref):
        """
        Initialize the video grid panel.

        Args:
            parent: Parent wx.Window
            client_ref: Client instance for server communication
        """
        super().__init__(parent)
        self.media_data = []
        self.client_ref = client_ref

        self._init_ui()

        # AUTO-LOAD videos immediately when panel opens
        wx.CallAfter(self.on_load_media, None)

    def _init_ui(self):
        """Initialize the user interface."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Scrollable grid
        self.scroll = self._create_scroll_window()
        main_sizer.Add(self.scroll, 1, wx.EXPAND | wx.ALL, SPACING_SCROLL)

        self.SetSizer(main_sizer)

    def _create_scroll_window(self):
        """
        Create scrollable window with grid sizer.

        Returns:
            wx.ScrolledWindow: Configured scroll window
        """
        scroll = wx.ScrolledWindow(self, style=wx.VSCROLL)
        scroll.SetScrollRate(SCROLL_RATE_X, SCROLL_RATE_Y)

        # GridSizer for displaying media
        self.grid_sizer = wx.GridSizer(
            cols=GRID_COLUMNS,
            hgap=GRID_GAP,
            vgap=GRID_GAP
        )
        scroll.SetSizer(self.grid_sizer)

        return scroll

    def on_load_media(self, event):
        """
        Load videos from server.

        Args:
            event: wx.Event
        """
        try:
            # Request server to start video thumbnail server
            if not self._request_video_server_start():
                return

            # Wait for server to start
            time.sleep(SERVER_START_DELAY)

            # Fetch video data from thumbnail server
            self.media_data = self._fetch_videos_from_thumbnail_server()

            # Display in grid
            self.display_media()

        except Exception as e:
            self._show_error(f"Error connecting to server: {e}")

    def _request_video_server_start(self):
        """
        Request main server to start video thumbnail server.

        Returns:
            bool: True if successful, False otherwise
        """
        response = self.client_ref._send_request('GET_ALL_VIDEOS_GRID', {})

        if response.get('status') != 'success':
            self._show_error(
                f"Failed to start video server: "
                f"{response.get('message', 'Unknown error')}"
            )
            return False

        return True

    def _fetch_videos_from_thumbnail_server(self):
        """
        Connect to thumbnail server and fetch video data.

        Returns:
            list: Video data with thumbnails
        """
        # Connect to video thumbnail server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, VIDEO_THUMBNAIL_PORT))

        # Send request
        sock.sendall("GET_VIDEOS_MEDIA".encode('utf-8'))

        # Receive response
        response = self._receive_full_response(sock)
        sock.close()

        # Decode and return
        return json.loads(response.decode('utf-8'))

    def _receive_full_response(self, sock):
        """
        Receive complete response from socket.

        Args:
            sock: Socket to receive from

        Returns:
            bytes: Complete response data
        """
        response = b""
        while True:
            chunk = sock.recv(RECV_BUFFER_SIZE)
            if not chunk:
                break
            response += chunk
        return response

    def display_media(self):
        """Display videos in grid."""
        # Clear previous grid
        self.grid_sizer.Clear(True)

        # Add each video
        for media_item in self.media_data:
            media_panel = self._create_video_panel(media_item)
            self.grid_sizer.Add(media_panel, 0, wx.EXPAND)

        # Update layout
        self.scroll.Layout()
        self.scroll.FitInside()

    def _create_video_panel(self, media_item):
        """
        Create panel for single video item.

        Args:
            media_item: Video data dictionary

        Returns:
            wx.Panel: Video display panel
        """
        panel = wx.Panel(self.scroll, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(COLOR_PANEL_BACKGROUND)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Thumbnail
        thumbnail = self._create_thumbnail(panel, media_item)
        sizer.Add(thumbnail, 0, wx.ALL | wx.CENTER, SPACING_THUMBNAIL)

        # Title
        title_label = self._create_title_label(panel, media_item)
        sizer.Add(title_label, 0, wx.ALL | wx.CENTER, SPACING_THUMBNAIL)

        # Metadata
        self._add_metadata_labels(panel, sizer, media_item)

        panel.SetSizer(sizer)
        panel.Fit()

        return panel

    def _create_thumbnail(self, parent, media_item):
        """
        Create thumbnail image from base64 data.

        Args:
            parent: Parent widget
            media_item: Video data dictionary

        Returns:
            wx.StaticBitmap: Thumbnail widget
        """
        # Decode base64 image
        img_data = base64.b64decode(media_item['thumbnail'])
        img_stream = io.BytesIO(img_data)
        img = wx.Image(img_stream)

        # Resize to standard size
        img = img.Scale(THUMBNAIL_SIZE, THUMBNAIL_SIZE, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(img)

        # Create clickable bitmap
        img_ctrl = wx.StaticBitmap(parent, bitmap=bitmap)
        img_ctrl.Bind(
            wx.EVT_LEFT_DCLICK,
            lambda evt: self.on_video_double_click(media_item)
        )
        img_ctrl.SetCursor(wx.Cursor(wx.CURSOR_HAND))

        return img_ctrl

    def _create_title_label(self, parent, media_item):
        """
        Create title label for video.

        Args:
            parent: Parent widget
            media_item: Video data dictionary

        Returns:
            wx.StaticText: Title label
        """
        label_text = media_item['name']

        label = wx.StaticText(parent, label=label_text)
        label.SetFont(
            wx.Font(
                FONT_SIZE_TITLE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL
            )
        )
        label.Bind(
            wx.EVT_LEFT_DCLICK,
            lambda evt: self.on_video_double_click(media_item)
        )
        label.SetCursor(wx.Cursor(wx.CURSOR_HAND))

        return label

    def _add_metadata_labels(self, parent, sizer, media_item):
        """
        Add metadata labels (category, level, uploader).

        Args:
            parent: Parent widget
            sizer: Sizer to add to
            media_item: Video data dictionary
        """
        metadata_font = wx.Font(
            FONT_SIZE_METADATA,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_ITALIC,
            wx.FONTWEIGHT_NORMAL
        )

        # Category
        category_label = wx.StaticText(
            parent,
            label=f"Category: {media_item.get('category', 'N/A')}"
        )
        category_label.SetFont(metadata_font)
        sizer.Add(category_label, 0, wx.ALL | wx.CENTER, SPACING_METADATA)

        # Level
        level_label = wx.StaticText(
            parent,
            label=f"Level: {media_item.get('level', 'N/A')}"
        )
        level_label.SetFont(metadata_font)
        sizer.Add(level_label, 0, wx.ALL | wx.CENTER, SPACING_METADATA)

        # Uploader
        uploader_label = wx.StaticText(
            parent,
            label=f"By: {media_item.get('uploader', 'Unknown')}"
        )
        uploader_label.SetFont(metadata_font)
        sizer.Add(uploader_label, 0, wx.ALL | wx.CENTER, SPACING_METADATA)

    def on_video_double_click(self, media_item):
        """
        Handle double click on video - open interaction frame.

        Args:
            media_item: Video data dictionary
        """
        video_title = media_item['name']
        print(f"Opening interaction for: {video_title}")

        # Prepare video data
        video_data = {
            'title': video_title,
            'category': media_item.get('category', 'N/A'),
            'level': media_item.get('level', 'N/A'),
            'uploader': media_item.get('uploader', 'Unknown'),
            'path': media_item['path']
        }

        # Open interaction window after current event
        wx.CallAfter(self._open_interaction_window, video_data)

    def _open_interaction_window(self, video_data):
        """
        Open video interaction window and hide grid.

        Args:
            video_data: Video information dictionary
        """
        # Get reference to grid frame
        parent_frame = self.GetTopLevelParent()

        if parent_frame:
            print(f"[DEBUG] Hiding grid window: {parent_frame.GetTitle()}")
            parent_frame.Hide()

        # Open interaction frame
        VideoInteractionFrame(
            self.client_ref,
            video_data,
            parent_window=parent_frame
        )

    def _show_error(self, message):
        """
        Show error message dialog.

        Args:
            message: Error message to display
        """
        wx.MessageBox(message, "Error", wx.OK | wx.ICON_ERROR)