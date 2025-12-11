import wx
from Show_all_videos_in_wx import run as show_all_videos
import UploadVideoFrame


class VideoMenuFrame(wx.Frame):
    """
    Video menu - shows options for viewing or uploading videos.
    Can return to parent menu (MainMenuFrame).
    """

    def __init__(self, client, parent_menu=None):
        super().__init__(parent=None, title="Videos Menu", size=(400, 300))

        self.client = client
        self.parent_menu = parent_menu  # Reference to MainMenuFrame

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Videos")
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT,
                             wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        # --- Buttons ---
        view_btn = wx.Button(panel, label="🎬 View all videos (Grid)", size=(250, 40))
        upload_btn = wx.Button(panel, label="📤 Upload a new video", size=(250, 40))
        back_btn = wx.Button(panel, label="⬅️ Back to Main Menu", size=(250, 40))

        view_btn.Bind(wx.EVT_BUTTON, self.on_view)
        upload_btn.Bind(wx.EVT_BUTTON, self.on_upload)
        back_btn.Bind(wx.EVT_BUTTON, self.on_back)

        vbox.Add(view_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=20)
        vbox.Add(upload_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=15)
        vbox.Add(back_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=25)

        panel.SetSizer(vbox)
        self.Centre()
        self.Show()

    def on_view(self, event):
        """Open video grid view and hide this menu"""
        self.Hide()  # Hide this window
        show_all_videos(self.client, parent_menu=self)

    def on_upload(self, event):
        """Open upload window"""
        # Don't close this window - just open upload dialog
        UploadVideoFrame.UploadVideoFrame(client=self.client)

    def on_back(self, event):
        """Return to main menu"""
        self.Close()

        # Show parent menu if it exists
        if self.parent_menu:
            self.parent_menu.Show()