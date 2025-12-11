import wx
import os


class UploadVideoFrame(wx.Frame):
    """
    GUI window for uploading a new video.
    Uses the client's _send_request() to communicate with the server.
    """

    def __init__(self, client):
        super().__init__(parent=None, title="Upload Video", size=(450, 300))

        self.client = client
        self.selected_file_path = None

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title
        lbl_title = wx.StaticText(panel, label="Upload a New Video")
        lbl_title.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT,
                                  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        vbox.Add(lbl_title, 0, wx.ALIGN_CENTER | wx.TOP, 15)

        # File selection button
        btn_choose = wx.Button(panel, label="Choose Video File")
        btn_choose.Bind(wx.EVT_BUTTON, self.on_choose_file)
        vbox.Add(btn_choose, 0, wx.ALIGN_CENTER | wx.TOP, 15)

        # Display selected filename
        self.file_label = wx.StaticText(panel, label="No file selected")
        vbox.Add(self.file_label, 0, wx.ALIGN_CENTER | wx.TOP, 10)

        # Category field
        hbox_cat = wx.BoxSizer(wx.HORIZONTAL)
        hbox_cat.Add(wx.StaticText(panel, label="Category:"), 0, wx.ALL, 5)
        self.txt_category = wx.TextCtrl(panel)
        hbox_cat.Add(self.txt_category, 1, wx.ALL | wx.EXPAND, 5)
        vbox.Add(hbox_cat, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)

        # Level field
        hbox_lvl = wx.BoxSizer(wx.HORIZONTAL)
        hbox_lvl.Add(wx.StaticText(panel, label="Level:"), 0, wx.ALL, 5)
        self.txt_level = wx.TextCtrl(panel)
        hbox_lvl.Add(self.txt_level, 1, wx.ALL | wx.EXPAND, 5)
        vbox.Add(hbox_lvl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)

        # Upload button
        btn_upload = wx.Button(panel, label="Upload Video")
        btn_upload.Bind(wx.EVT_BUTTON, self.on_upload)
        vbox.Add(btn_upload, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 20)

        panel.SetSizer(vbox)
        self.Centre()
        self.Show()

    def on_choose_file(self, event):
        """Open file dialog to pick a video file."""
        with wx.FileDialog(self,
                           "Choose a video file",
                           wildcard="Video files (*.mp4;*.mov;*.avi)|*.mp4;*.mov;*.avi",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:

            if dialog.ShowModal() == wx.ID_CANCEL:
                return

            self.selected_file_path = dialog.GetPath()
            self.file_label.SetLabel(f"Selected: {os.path.basename(self.selected_file_path)}")

    def on_upload(self, event):
        """Send video metadata + file content to the server."""
        if not self.selected_file_path:
            wx.MessageBox("Please choose a video file.", "Error", wx.OK | wx.ICON_ERROR)
            return

        category = self.txt_category.GetValue().strip()
        level = self.txt_level.GetValue().strip()

        if not category or not level:
            wx.MessageBox("Please fill all fields.", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Read file bytes
        try:
            with open(self.selected_file_path, "rb") as f:
                file_bytes = f.read()
        except Exception as e:
            wx.MessageBox(f"Error reading file:\n{e}", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Prepare request
        request_payload = {
            "title": os.path.basename(self.selected_file_path),
            "category": category,
            "level": level,
            "file_data": file_bytes.hex(),  # hex so JSON can transfer large binary data
        }

        # Send to server
        response = self.client._send_request("UPLOAD_VIDEO", request_payload)

        if response.get("status") == "success":
            wx.MessageBox("Video uploaded successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
            self.Close()
        else:
            error_msg = response.get("message", "Server error.")
            wx.MessageBox(f"Upload failed:\n{error_msg}", "Error", wx.OK | wx.ICON_ERROR)

