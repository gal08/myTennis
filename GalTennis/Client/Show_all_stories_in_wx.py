import wx
import socket
import json
import base64
import io
import Read_server_ip


class VideoGridPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.videos_data = []

        # Create interface
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Button to load videos
        btn_load = wx.Button(self, label="Load Videos from Server")
        btn_load.Bind(wx.EVT_BUTTON, self.on_load_videos)
        main_sizer.Add(btn_load, 0, wx.ALL | wx.CENTER, 10)

        # ScrolledWindow for video grid
        self.scroll = wx.ScrolledWindow(self, style=wx.VSCROLL)
        self.scroll.SetScrollRate(0, 20)

        # GridSizer for displaying videos
        self.grid_sizer = wx.GridSizer(cols=3, hgap=10, vgap=10)
        self.scroll.SetSizer(self.grid_sizer)

        main_sizer.Add(self.scroll, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(main_sizer)

    def on_load_videos(self, event):
        """Load videos from server"""
        try:
            # Connect to server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ip = Read_server_ip.readServerIp()
            sock.connect((ip, 2222))

            # Send request
            sock.sendall("GET_VIDEOS".encode('utf-8'))

            # Receive response
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk

            sock.close()

            # Decode response
            self.videos_data = json.loads(response.decode('utf-8'))

            # Display videos
            self.display_videos()

        except Exception as e:
            wx.MessageBox(f"Error connecting to server: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def display_videos(self):
        """Display videos in grid"""
        # Clear previous grid
        self.grid_sizer.Clear(True)

        for video_data in self.videos_data:
            # Create panel for each video
            video_panel = self.create_video_panel(video_data)
            self.grid_sizer.Add(video_panel, 0, wx.EXPAND)

        self.scroll.Layout()
        self.scroll.FitInside()

    def create_video_panel(self, video_data):
        """Create individual panel for video"""
        panel = wx.Panel(self.scroll, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Convert image from base64
        img_data = base64.b64decode(video_data['thumbnail'])
        img_stream = io.BytesIO(img_data)
        img = wx.Image(img_stream)

        # Resize to square
        img = img.Scale(200, 200, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(img)

        # Create StaticBitmap
        img_ctrl = wx.StaticBitmap(panel, bitmap=bitmap)
        img_ctrl.Bind(wx.EVT_LEFT_DCLICK, lambda evt: self.on_video_double_click(video_data))
        img_ctrl.SetCursor(wx.Cursor(wx.CURSOR_HAND))

        sizer.Add(img_ctrl, 0, wx.ALL | wx.CENTER, 5)

        # Video name
        label = wx.StaticText(panel, label=video_data['name'])
        label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        label.Bind(wx.EVT_LEFT_DCLICK, lambda evt: self.on_video_double_click(video_data))
        label.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        sizer.Add(label, 0, wx.ALL | wx.CENTER, 5)

        panel.SetSizer(sizer)
        panel.Fit()

        return panel

    def on_video_double_click(self, video_data):
        """Handle double click on video - add your logic here"""
        print(f"Double clicked on: {video_data['name']}")
        print(f"Full path: {video_data['path']}")

        # Add your code here to handle the video
        # For example: open separate window, play video, edit, etc.

        wx.MessageBox(f"Double clicked on:\n{video_data['name']}", "Double Click", wx.OK | wx.ICON_INFORMATION)


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Video Display System", size=(800, 600))

        # Create main panel
        panel = VideoGridPanel(self)

        self.Centre()
        self.Show()


def run():
    app = wx.App()
    frame = MainFrame()
    app.MainLoop()
