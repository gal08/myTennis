"""
Gal Haham
Video menu frame - provides options for viewing and uploading videos.
Serves as navigation hub for video-related features.
REFACTORED: Improved documentation, better UI organization.
"""
import wx
from Show_all_videos_in_wx import run as show_all_videos
import UploadVideoFrame


class VideoMenuFrame(wx.Frame):
    """
    Video menu - shows options for viewing or uploading videos.

    Features:
    - View all videos in grid
    - Upload new video
    - Return to main menu

    REFACTORED: Split UI creation, improved documentation.
    """

    def __init__(self, client, parent_menu=None):
        """
        Initialize the video menu frame.

        Args:
            client: Client instance for server communication
            parent_menu: Reference to MainMenuFrame (optional)
        """
        super().__init__(parent=None, title="🎬 Videos Menu", size=(400, 300))

        self.client = client
        self.parent_menu = parent_menu

        self._init_ui()

        self.Centre()
        self.Show()

    def _init_ui(self):
        """Initialize the user interface."""
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        self._add_title(panel, vbox)

        # Buttons
        self._add_buttons(panel, vbox)

        panel.SetSizer(vbox)

    def _add_title(self, panel, vbox):
        """
        Add title section.

        Args:
            panel: Parent panel
            vbox: Vertical sizer
        """
        title = wx.StaticText(panel, label="Videos")
        title_font = wx.Font(
            16,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALIGN_CENTER | wx.TOP, border=20)

    def _add_buttons(self, panel, vbox):
        """
        Add menu buttons.

        Args:
            panel: Parent panel
            vbox: Vertical sizer
        """
        # View all videos button
        view_btn = wx.Button(
            panel,
            label="View all videos (Grid)",
            size=(250, 40)
        )
        view_btn.Bind(wx.EVT_BUTTON, self.on_view)
        vbox.Add(view_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        # Upload button
        upload_btn = wx.Button(
            panel,
            label="Upload a new video",
            size=(250, 40)
        )
        upload_btn.Bind(wx.EVT_BUTTON, self.on_upload)
        vbox.Add(upload_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=15)

        # Back button
        back_btn = wx.Button(
            panel,
            label="⬅️ Back to Main Menu",
            size=(250, 40)
        )
        back_btn.Bind(wx.EVT_BUTTON, self.on_back)
        vbox.Add(back_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=25)

    def on_view(self, event):
        """
        Open video grid view and hide this menu.

        Args:
            event: wx.Event
        """
        self.Hide()
        show_all_videos(self.client, parent_menu=self)

    def on_upload(self, event):
        """
        Open upload window without closing this menu.

        Args:
            event: wx.Event
        """
        UploadVideoFrame.UploadVideoFrame(client=self.client)

    def on_back(self, event):
        """
        Return to main menu.

        Args:
            event: wx.Event
        """
        self.Close()

        # Show parent menu if it exists
        if self.parent_menu:
            self.parent_menu.Show()
