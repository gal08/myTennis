import wx
import VideoListFrame
import UploadVideoFrame


class VideoMenuFrame(wx.Frame):
    def __init__(self, client):
        super().__init__(parent=None, title="Videos Menu", size=(400, 300))

        self.client = client

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Videos")
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT,
                             wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        vbox.Add(title, flag=wx.ALIGN_CENTER | wx.TOP, border=20)

        # --- Buttons ---
        view_btn = wx.Button(panel, label="View all videos", size=(200, 40))
        upload_btn = wx.Button(panel, label="Upload a new video", size=(200, 40))
        back_btn = wx.Button(panel, label="Back", size=(200, 40))

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
        self.Close()
        VideoListFrame.VideoListFrame(client=self.client)

    def on_upload(self, event):
        self.Close()
        UploadVideoFrame.UploadVideoFrame(client=self.client)

    def on_back(self, event):
        self.Close()
