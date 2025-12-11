import wx
from Video_Player_Client import run_video_player_client
from Show_all_stories_in_wx import MainFrame as ShowAllStoriesFrame
from Story_camera import StoryCameraFrame
from VideoMenuFrame import VideoMenuFrame
from StoriesMenuFrame import StoriesMenuFrame


class MainMenuFrame(wx.Frame):
    """
    Main GUI menu after login.
    Closes itself when opening sub-menus to avoid window stacking.
    """

    def __init__(self, username, client_ref):
        super().__init__(parent=None, title="Main Menu", size=(400, 300))

        self.username = username
        self.client_ref = client_ref

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
        """Open Videos menu and hide main menu"""
        self.Hide()  # Hide instead of Close to keep app running
        VideoMenuFrame(client=self.client_ref, parent_menu=self)

    def on_stories(self, event):
        """Open Stories menu and hide main menu"""
        self.Hide()  # Hide instead of Close to keep app running
        StoriesMenuFrame(username=self.username, client_ref=self.client_ref, parent_menu=self)

    def on_quit(self, event):
        """Quit application"""
        self.close_application()

    def close_application(self):
        """Properly close the entire application"""
        # Show styled goodbye dialog first
        dialog = self.create_goodbye_dialog()
        dialog.Show()

        # Schedule cleanup after dialog is visible
        wx.CallLater(2000, lambda: self.finish_closing(dialog))

    def finish_closing(self, dialog):
        """Complete the closing process after dialog has been shown"""
        dialog.Close()

        # Close ALL windows
        for window in wx.GetTopLevelWindows():
            if window != self and window != dialog:
                window.Close(True)

        self.Destroy()
        app = wx.App.Get()
        if app:
            app.ExitMainLoop()

        # Force exit after cleanup
        wx.CallLater(500, self._force_exit)

    def create_goodbye_dialog(self):
        """Create and return a styled goodbye message dialog"""
        # Create a custom dialog
        dialog = wx.Dialog(
            self,
            title="Tennis Social",
            size=(450, 300),
            style=wx.CAPTION | wx.STAY_ON_TOP
        )
        dialog.SetBackgroundColour(wx.Colour(245, 245, 245))

        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Top panel with gradient effect (dark green)
        top_panel = wx.Panel(dialog)
        top_panel.SetBackgroundColour(wx.Colour(40, 120, 80))
        top_sizer = wx.BoxSizer(wx.VERTICAL)

        # Tennis emoji/icon
        icon_text = wx.StaticText(top_panel, label="🎾")
        icon_font = wx.Font(48, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        icon_text.SetFont(icon_font)
        top_sizer.Add(icon_text, 0, wx.ALIGN_CENTER | wx.TOP, 20)

        # Title
        title = wx.StaticText(top_panel, label="Tennis Social")
        title.SetForegroundColour(wx.WHITE)
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        top_sizer.Add(title, 0, wx.ALIGN_CENTER | wx.TOP, 10)

        top_panel.SetSizer(top_sizer)
        main_sizer.Add(top_panel, 1, wx.EXPAND)

        # Bottom panel with message
        bottom_panel = wx.Panel(dialog)
        bottom_panel.SetBackgroundColour(wx.Colour(245, 245, 245))
        bottom_sizer = wx.BoxSizer(wx.VERTICAL)

        # Goodbye message
        goodbye_text = wx.StaticText(
            bottom_panel,
            label="Goodbye!"
        )
        goodbye_text.SetForegroundColour(wx.Colour(40, 120, 80))
        goodbye_font = wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        goodbye_text.SetFont(goodbye_font)
        bottom_sizer.Add(goodbye_text, 0, wx.ALIGN_CENTER | wx.TOP, 25)

        # Thank you message
        thanks_text = wx.StaticText(
            bottom_panel,
            label="Thanks for using Tennis Social!"
        )
        thanks_text.SetForegroundColour(wx.Colour(100, 100, 100))
        thanks_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        thanks_text.SetFont(thanks_font)
        bottom_sizer.Add(thanks_text, 0, wx.ALIGN_CENTER | wx.TOP, 10)

        # Username specific message
        user_text = wx.StaticText(
            bottom_panel,
            label=f"See you next time, {self.username}! 👋"
        )
        user_text.SetForegroundColour(wx.Colour(150, 150, 150))
        user_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
        user_text.SetFont(user_font)
        bottom_sizer.Add(user_text, 0, wx.ALIGN_CENTER | wx.TOP, 15)

        bottom_panel.SetSizer(bottom_sizer)
        main_sizer.Add(bottom_panel, 1, wx.EXPAND)

        dialog.SetSizer(main_sizer)
        dialog.Centre()

        # Return the dialog (caller will show it)
        return dialog

    def _force_exit(self):
        """Force exit to close all threads"""
        import sys
        sys.exit(0)