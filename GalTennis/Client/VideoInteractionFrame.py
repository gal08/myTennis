import wx
from Video_Player_Client import run_video_player_client


class VideoInteractionFrame(wx.Frame):
    """
    GUI for selecting actions on a single video:
    Play / Like / Comments
    """

    def __init__(self, client, video_data):
        super().__init__(parent=None, title=f"Video: {video_data['title']}", size=(400, 350))

        self.client = client
        self.video = video_data

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(panel, label=f"Selected: {self.video['title']}")
        title_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        vbox.Add(title, 0, wx.ALIGN_CENTER | wx.TOP, 20)

        # Buttons
        play_btn = wx.Button(panel, label="Play Video", size=(200, 40))
        like_btn = wx.Button(panel, label="Like / Unlike", size=(200, 40))
        comments_btn = wx.Button(panel, label="View / Add Comments", size=(200, 40))
        back_btn = wx.Button(panel, label="Back", size=(200, 40))

        play_btn.Bind(wx.EVT_BUTTON, self.on_play)
        like_btn.Bind(wx.EVT_BUTTON, self.on_like)
        comments_btn.Bind(wx.EVT_BUTTON, self.on_comments)
        back_btn.Bind(wx.EVT_BUTTON, self.on_back)

        vbox.Add(play_btn, 0, wx.ALIGN_CENTER | wx.TOP, 15)
        vbox.Add(like_btn, 0, wx.ALIGN_CENTER | wx.TOP, 15)
        vbox.Add(comments_btn, 0, wx.ALIGN_CENTER | wx.TOP, 15)
        vbox.Add(back_btn, 0, wx.ALIGN_CENTER | wx.TOP, 20)

        panel.SetSizer(vbox)

        self.Centre()
        self.Show()

    # -------------------------------
    # Button Handlers
    # -------------------------------

    def on_play(self, event):
        run_video_player_client()

    def on_like(self, event):
        res = self.client.toggle_like(self.video['title'])
        msg = res.get("message", "Updated like status.")
        wx.MessageBox(msg, "Like / Unlike", wx.OK | wx.ICON_INFORMATION)

    def on_comments(self, event):
        # TODO: implement a full comments GUI window
        wx.MessageBox("Comments GUI will be added here.", "Comments", wx.OK)

    def on_back(self, event):
        self.Close()
