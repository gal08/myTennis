import wx
import VideoMenuFrame
from VideoInteractionFrame import VideoInteractionFrame


class VideoListFrame(wx.Frame):
    def __init__(self, client):
        super().__init__(parent=None, title="Available Videos", size=(600, 400))

        self.client = client

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # --- Title ---
        title = wx.StaticText(panel, label="Available Videos")
        title.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT,
                             wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        vbox.Add(title, flag=wx.ALIGN_CENTER | wx.TOP, border=10)

        # --- Fetch videos from server ---
        response = self.client._send_request("GET_VIDEOS", {})

        if response.get("status") != "success":
            wx.MessageBox("Failed to load videos", "Error", wx.OK | wx.ICON_ERROR)
            self.Close()
            return

        videos = response.get("videos", [])

        self.videos = videos

        # --- List Control ---
        self.listbox = wx.ListBox(panel, choices=[
            f"{i+1}. {v['title']} | {v['category']} | {v['level']} | {v['uploader']}"
            for i, v in enumerate(videos)
        ], size=(540, 250))

        vbox.Add(self.listbox, flag=wx.ALL | wx.CENTER, border=15)

        # --- Buttons ---
        buttons = wx.BoxSizer(wx.HORIZONTAL)

        select_btn = wx.Button(panel, label="Select")
        back_btn = wx.Button(panel, label="Back")

        select_btn.Bind(wx.EVT_BUTTON, self.on_select)
        back_btn.Bind(wx.EVT_BUTTON, self.on_back)

        buttons.Add(select_btn, 0, wx.RIGHT, 10)
        buttons.Add(back_btn, 0)

        vbox.Add(buttons, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=20)

        panel.SetSizer(vbox)
        self.Centre()
        self.Show()

    def on_select(self, event):
        sel = self.listbox.GetSelection()
        if sel == wx.NOT_FOUND:
            wx.MessageBox("Please select a video first", "Error", wx.OK | wx.ICON_WARNING)
            return

        selected_video = self.videos[sel]
        VideoInteractionFrame(client=self.client, video_data=selected_video)

    def on_back(self, event):
        VideoMenuFrame.VideoMenuFrame(client=self.client)
        self.Close()
