import wx
from Show_all_stories_in_wx import run as show_all_stories
from Story_camera import StoryCameraFrame


class StoriesMenuFrame(wx.Frame):
    """
    GUI menu for Stories functionality.
    Can return to parent menu (MainMenuFrame).
    """

    def __init__(self, username, client_ref, parent_menu=None):
        super().__init__(parent=None, title="Stories Menu", size=(400, 350))

        self.username = username
        self.client_ref = client_ref
        self.parent_menu = parent_menu  # Reference to MainMenuFrame

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(245, 245, 245))
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(panel, label="📸 Stories")
        title.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT,
                              wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title.SetForegroundColour(wx.Colour(40, 120, 80))
        vbox.Add(title, flag=wx.ALIGN_CENTER | wx.TOP, border=30)

        subtitle = wx.StaticText(panel, label=f"Welcome, {self.username}!")
        subtitle.SetForegroundColour(wx.Colour(100, 100, 100))
        vbox.Add(subtitle, flag=wx.ALIGN_CENTER | wx.TOP, border=5)

        btn_post = wx.Button(panel, label="📷 Post New Story (Camera)", size=(250, 45))
        btn_post.Bind(wx.EVT_BUTTON, self.on_post_story)

        btn_view_all = wx.Button(panel, label="🎬 View All Stories", size=(250, 45))
        btn_view_all.Bind(wx.EVT_BUTTON, self.on_view_all_stories)

        btn_back = wx.Button(panel, label="⬅️ Back to Main Menu", size=(250, 45))
        btn_back.Bind(wx.EVT_BUTTON, self.on_back)

        # Add buttons to layout
        vbox.Add(btn_post, flag=wx.ALIGN_CENTER | wx.TOP, border=15)
        vbox.Add(btn_view_all, flag=wx.ALIGN_CENTER | wx.TOP, border=15)
        vbox.Add(btn_back, flag=wx.ALIGN_CENTER | wx.TOP, border=25)

        panel.SetSizer(vbox)
        self.Centre()
        self.Show()

    # -------------------------------------------------
    # Handlers
    # -------------------------------------------------

    def on_view_all_stories(self, event):
        """Opens GUI for viewing ALL stories."""
        self.Hide()  # Hide this menu

        response = self.client_ref._send_request('GET_IMAGES_OF_ALL_VIDEOS', {})
        print(response)

        show_all_stories(self.client_ref, parent_menu=self)

    def on_post_story(self, event):
        """Opens the camera window to post a story."""

        def on_post_callback(caption, media_type, media_data):
            self.client_ref.on_story_post_callback(caption, media_type, media_data)

        def on_closed_callback():
            print("[INFO] Camera window closed")

        StoryCameraFrame(
            parent=None,
            username=self.username,
            on_post_callback=on_post_callback,
            closed_callback=on_closed_callback
        )

    def on_back(self, event):
        """Return to main menu"""
        self.Close()

        # Show parent menu if it exists
        if self.parent_menu:
            self.parent_menu.Show()