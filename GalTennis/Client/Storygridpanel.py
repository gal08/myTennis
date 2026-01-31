"""
Gal Haham
Story grid panel for displaying story thumbnails.
Shows images and videos in a scrollable grid layout.
REFACTORED: Separated class, all constants added, methods split.
"""
import time
import wx
import socket
import json
import base64
import io
from story_player_client import run_story_player_client
import key_exchange


# Server Configuration
SERVER_IP = '127.0.0.1'
STORY_THUMBNAIL_PORT = 2222

# Timing
TWO_SECOND_PAUSE = 2

# Grid Display
THUMBNAIL_SIZE = 200
GRID_COLUMNS = 3
GRID_GAP = 10

# Spacing
SPACING_SCROLL = 10
SPACING_THUMBNAIL = 5

# Scroll Configuration
SCROLL_RATE_X = 0
SCROLL_RATE_Y = 20

# Network
RECV_BUFFER_SIZE = 4096

# Colors
COLOR_PANEL_BACKGROUND = wx.Colour(240, 240, 240)

# Fonts
FONT_SIZE_LABEL = 9


class StoryGridPanel(wx.Panel):
    """
    Panel displaying grid of story thumbnails (images and videos).

    Features:
    - Load stories from server
    - Display in scrollable grid
    - Show thumbnails with type icons
    - Handle story playback

    REFACTORED: All magic numbers replaced with constants.
    """

    def __init__(self, parent, client_ref):
        """
        Initialize the story grid panel.

        Args:
            parent: Parent wx.Window
            client_ref: Client instance for server communication
        """
        super().__init__(parent)
        self.media_data = []
        self.client_ref = client_ref

        self._init_ui()

        # AUTO-LOAD stories immediately when panel opens
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
        Load stories from server.

        Args:
            event: wx.Event
        """
        try:
            # Fetch story data from thumbnail server
            self.media_data = self._fetch_stories_from_server()

            # Display in grid
            self.display_media()

        except Exception as e:
            self._show_error(f"Error connecting to server: {e}")

    def _fetch_stories_from_server(self):
        """
        Connect to story thumbnail server and fetch data.

        Returns:
            list: Story data with thumbnails
        """
        # Connect to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, STORY_THUMBNAIL_PORT))
        key = key_exchange.KeyExchange.send_recv_key((sock, None))
        conn = (sock, key)
        # Send request
        sock.sendall("GET_MEDIA".encode('utf-8'))

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
        """Display stories in grid."""
        # Clear previous grid
        self.grid_sizer.Clear(True)

        # Add each story
        for media_item in self.media_data:
            media_panel = self._create_story_panel(media_item)
            self.grid_sizer.Add(media_panel, 0, wx.EXPAND)

        # Update layout
        self.scroll.Layout()
        self.scroll.FitInside()

    def _create_story_panel(self, media_item):
        """
        Create panel for single story item.

        Args:
            media_item: Story data dictionary

        Returns:
            wx.Panel: Story display panel
        """
        panel = wx.Panel(self.scroll, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(COLOR_PANEL_BACKGROUND)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Thumbnail
        thumbnail = self._create_thumbnail(panel, media_item)
        sizer.Add(thumbnail, 0, wx.ALL | wx.CENTER, SPACING_THUMBNAIL)

        # Title with type icon
        title_label = self._create_title_label(panel, media_item)
        sizer.Add(title_label, 0, wx.ALL | wx.CENTER, SPACING_THUMBNAIL)

        panel.SetSizer(sizer)
        panel.Fit()

        return panel

    def _create_thumbnail(self, parent, media_item):
        """
        Create thumbnail image from base64 data.

        Args:
            parent: Parent widget
            media_item: Story data dictionary

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
            lambda evt: self.on_media_double_click(media_item)
        )
        img_ctrl.SetCursor(wx.Cursor(wx.CURSOR_HAND))

        return img_ctrl

    def _create_title_label(self, parent, media_item):
        """
        Create title label with type icon.

        Args:
            parent: Parent widget
            media_item: Story data dictionary

        Returns:
            wx.StaticText: Title label
        """
        label_text = media_item['name']

        label = wx.StaticText(parent, label=label_text)
        label.SetFont(
            wx.Font(
                FONT_SIZE_LABEL,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL
            )
        )
        label.Bind(
            wx.EVT_LEFT_DCLICK,
            lambda evt: self.on_media_double_click(media_item)
        )
        label.SetCursor(wx.Cursor(wx.CURSOR_HAND))

        return label

    def on_media_double_click(self, media_item):
        """
        Handle double click on story - play story.

        Args:
            media_item: Story data dictionary
        """
        story_name = media_item['name']

        print(f"Double clicked on: {story_name}")
        print(f"Type: {media_item['type']}")
        print(f"Full path: {media_item['path']}")

        try:
            # Request server to start story playback
            response = self._request_story_playback(story_name)

            if response.get('status') == 'success':
                # Wait for server to start
                time.sleep(TWO_SECOND_PAUSE)
                # Launch story player
                run_story_player_client()

        except Exception as e:
            self._show_error(f"Error starting story player: \n{str(e)}")

    def _request_story_playback(self, story_name):
        """
        Request server to start story playback.

        Args:
            story_name: Name of story file

        Returns:
            dict: Server response
        """
        return self.client_ref._send_request('PLAY_STORY', {
            'filename': story_name
        })

    def _show_error(self, message):
        """
        Show error message dialog.

        Args:
            message: Error message to display
        """
        wx.MessageBox(message, "Error", wx.OK | wx.ICON_ERROR)
