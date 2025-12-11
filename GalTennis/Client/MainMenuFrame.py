import wx
from Video_Player_Client import run_video_player_client
from Show_all_stories_in_wx import MainFrame as ShowAllStoriesFrame
from Story_camera import StoryCameraFrame
from VideoMenuFrame import VideoMenuFrame
from StoriesMenuFrame import StoriesMenuFrame


class MainMenuFrame(wx.Frame):
    """
    Main GUI menu after login.
    Replaces the console-based text menu.
    """

    def __init__(self, username, client_ref):
        super().__init__(parent=None, title="Main Menu", size=(400, 300))

        self.username = username
        self.client_ref = client_ref   # נשמור הפניה ל-client שלך

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label=f"Welcome, {self.username}!")
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT,
                             wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        # --- Buttons ---
        videos_btn = wx.Button(panel, label="Videos (View / Upload)", size=(200, 40))
        stories_btn = wx.Button(panel, label="Stories (View / Post)", size=(200, 40))
        quit_btn = wx.Button(panel, label="Quit", size=(200, 40))

        videos_btn.Bind(wx.EVT_BUTTON, self.on_videos)
        stories_btn.Bind(wx.EVT_BUTTON, self.on_stories)
        quit_btn.Bind(wx.EVT_BUTTON, self.on_quit)

        vbox.Add(videos_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=20)
        vbox.Add(stories_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=15)
        vbox.Add(quit_btn, flag=wx.ALIGN_CENTER | wx.TOP, border=25)

        panel.SetSizer(vbox)
        self.Centre()
        self.Show()

    # -------------------------
    # Button Handlers
    # -------------------------

    def on_videos(self, event):
        VideoMenuFrame(client=self.client_ref)

    def on_stories(self, event):
        StoriesMenuFrame(username=self.username, client_ref=self.client_ref)

    def on_quit(self, event):
        self.Close()
