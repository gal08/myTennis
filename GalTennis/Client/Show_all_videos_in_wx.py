import time

import wx
import socket
import json
import base64
import io
from Video_Player_Client import run_video_player_client

TWO_SECOND_PAUSE = 2


class VideoGridPanel(wx.Panel):
    def __init__(self, parent, client_ref):
        super().__init__(parent)
        self.media_data = []
        self.client_ref = client_ref

        # Create interface
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Button to load media
        btn_load = wx.Button(self, label="Load All Videos from Server")
        btn_load.Bind(wx.EVT_BUTTON, self.on_load_media)
        main_sizer.Add(btn_load, 0, wx.ALL | wx.CENTER, 10)

        # ScrolledWindow for media grid
        self.scroll = wx.ScrolledWindow(self, style=wx.VSCROLL)
        self.scroll.SetScrollRate(0, 20)

        # GridSizer for displaying media
        self.grid_sizer = wx.GridSizer(cols=3, hgap=10, vgap=10)
        self.scroll.SetSizer(self.grid_sizer)

        main_sizer.Add(self.scroll, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(main_sizer)

    def on_load_media(self, event):
        """Load videos from server"""
        try:
            # First, ask main server to start the video display server
            response = self.client_ref._send_request('GET_ALL_VIDEOS_GRID', {})

            if response.get('status') != 'success':
                wx.MessageBox(
                    f"Failed to start video server: {response.get('message', 'Unknown error')}",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
                return

            # Give server time to start
            import time
            time.sleep(1)

            # Connect to video thumbnail server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ip = '127.0.0.1'
            sock.connect((ip, 2223))  # Different port for videos

            # Send request
            sock.sendall("GET_VIDEOS_MEDIA".encode('utf-8'))

            # Receive response
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk

            sock.close()

            # Decode response
            self.media_data = json.loads(response.decode('utf-8'))

            # Display media
            self.display_media()

        except Exception as e:
            wx.MessageBox(f"Error connecting to server: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def display_media(self):
        """Display videos in grid"""
        # Clear previous grid
        self.grid_sizer.Clear(True)

        for media_item in self.media_data:
            # Create panel for each media item
            media_panel = self.create_media_panel(media_item)
            self.grid_sizer.Add(media_panel, 0, wx.EXPAND)

        self.scroll.Layout()
        self.scroll.FitInside()

    def create_media_panel(self, media_item):
        """Create individual panel for video item"""
        panel = wx.Panel(self.scroll, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Convert image from base64
        img_data = base64.b64decode(media_item['thumbnail'])
        img_stream = io.BytesIO(img_data)
        img = wx.Image(img_stream)

        # Resize to square
        img = img.Scale(200, 200, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(img)

        # Create StaticBitmap
        img_ctrl = wx.StaticBitmap(panel, bitmap=bitmap)
        img_ctrl.Bind(wx.EVT_LEFT_DCLICK, lambda evt: self.on_video_double_click(media_item))
        img_ctrl.SetCursor(wx.Cursor(wx.CURSOR_HAND))

        sizer.Add(img_ctrl, 0, wx.ALL | wx.CENTER, 5)

        # File name with video icon
        video_icon = "🎬"
        label_text = f"{video_icon} {media_item['name']}"

        label = wx.StaticText(panel, label=label_text)
        label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        label.Bind(wx.EVT_LEFT_DCLICK, lambda evt: self.on_video_double_click(media_item))
        label.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        sizer.Add(label, 0, wx.ALL | wx.CENTER, 5)

        # Add metadata labels
        category_label = wx.StaticText(panel, label=f"Category: {media_item.get('category', 'N/A')}")
        category_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        sizer.Add(category_label, 0, wx.ALL | wx.CENTER, 2)

        level_label = wx.StaticText(panel, label=f"Level: {media_item.get('level', 'N/A')}")
        level_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        sizer.Add(level_label, 0, wx.ALL | wx.CENTER, 2)

        uploader_label = wx.StaticText(panel, label=f"By: {media_item.get('uploader', 'Unknown')}")
        uploader_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        sizer.Add(uploader_label, 0, wx.ALL | wx.CENTER, 2)

        panel.SetSizer(sizer)
        panel.Fit()

        return panel

    def on_video_double_click(self, media_item):
        """Handle double click on video item - open interaction frame"""
        video_title = media_item['name']

        print(f"Opening interaction for: {video_title}")

        # Prepare video data for interaction frame
        video_data = {
            'title': video_title,
            'category': media_item.get('category', 'N/A'),
            'level': media_item.get('level', 'N/A'),
            'uploader': media_item.get('uploader', 'Unknown'),
            'path': media_item['path']
        }

        # Use CallAfter to properly sequence window operations
        def open_interaction_window():
            # Get reference to grid frame before hiding it
            parent_frame = self.GetTopLevelParent()

            if parent_frame:
                print(f"[DEBUG] Hiding grid window: {parent_frame.GetTitle()}")
                parent_frame.Hide()  # Hide instead of Close!

            # Open the interaction frame with parent reference
            from VideoInteractionFrame import VideoInteractionFrame
            VideoInteractionFrame(self.client_ref, video_data, parent_window=parent_frame)

        # Schedule window transition after current event completes
        wx.CallAfter(open_interaction_window)


class MainFrame(wx.Frame):
    def __init__(self, client_ref, parent_menu=None):
        super().__init__(None, title="All Videos Display", size=(800, 600))

        self.client_ref = client_ref
        self.parent_menu = parent_menu  # Reference to VideoMenuFrame

        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close_window)

        # Create main panel
        panel = VideoGridPanel(self, client_ref)

        self.Centre()
        self.Show()

    def on_close_window(self, event):
        """Handle window close - return to videos menu"""
        # Show parent menu if it exists
        if self.parent_menu:
            self.parent_menu.Show()

        # Continue with close
        event.Skip()


def run(client_ref, parent_menu=None):
    # Don't create new app - use existing one!
    frame = MainFrame(client_ref, parent_menu=parent_menu)
    # Don't call app.MainLoop() - we're already in one!
