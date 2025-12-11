import wx
import os
import shutil


class UploadVideoFrame(wx.Frame):
    """
    GUI window for uploading a new video.

    Upload Process:
    1. User selects video file from their computer
    2. File is COPIED to server's videos/ folder
    3. Metadata (title, category, level) is saved to database

    Note: This assumes client and server share the same file system,
    or files are manually placed in the videos/ folder.
    """

    def __init__(self, client):
        super().__init__(parent=None, title="📤 Upload Video", size=(550, 450))

        self.client = client
        self.selected_file_path = None

        # Set background
        self.SetBackgroundColour(wx.Colour(245, 245, 245))

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(245, 245, 245))
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Header
        header_panel = wx.Panel(panel)
        header_panel.SetBackgroundColour(wx.Colour(76, 175, 80))
        header_sizer = wx.BoxSizer(wx.VERTICAL)

        lbl_title = wx.StaticText(header_panel, label="📤 Upload New Video")
        lbl_title.SetForegroundColour(wx.WHITE)
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        lbl_title.SetFont(title_font)
        header_sizer.Add(lbl_title, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        header_panel.SetSizer(header_sizer)
        vbox.Add(header_panel, 0, wx.EXPAND)

        # Instructions
        instructions = wx.StaticText(
            panel,
            label="Select a video file and provide details:"
        )
        instructions.SetForegroundColour(wx.Colour(100, 100, 100))
        vbox.Add(instructions, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        # File selection section
        file_panel = wx.Panel(panel)
        file_panel.SetBackgroundColour(wx.WHITE)
        file_sizer = wx.BoxSizer(wx.VERTICAL)

        btn_choose = wx.Button(file_panel, label="📁 Choose Video File", size=(250, 40))
        btn_choose.SetBackgroundColour(wx.Colour(0, 123, 255))
        btn_choose.SetForegroundColour(wx.WHITE)
        btn_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        btn_choose.SetFont(btn_font)
        btn_choose.Bind(wx.EVT_BUTTON, self.on_choose_file)
        file_sizer.Add(btn_choose, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        self.file_label = wx.StaticText(file_panel, label="No file selected")
        self.file_label.SetForegroundColour(wx.Colour(150, 150, 150))
        file_sizer.Add(self.file_label, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        file_panel.SetSizer(file_sizer)
        vbox.Add(file_panel, 0, wx.EXPAND | wx.ALL, 10)

        # Form section
        form_panel = wx.Panel(panel)
        form_panel.SetBackgroundColour(wx.WHITE)
        form_sizer = wx.BoxSizer(wx.VERTICAL)

        # Category field with dropdown
        cat_label = wx.StaticText(form_panel, label="Category:")
        cat_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        form_sizer.Add(cat_label, 0, wx.LEFT | wx.TOP, 15)

        categories = ['forehand', 'backhand', 'serve', 'slice', 'volley', 'smash']
        self.category_choice = wx.Choice(form_panel, choices=categories, size=(250, 30))
        self.category_choice.SetSelection(0)  # Default to first option
        form_sizer.Add(self.category_choice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        # Level field with dropdown
        lvl_label = wx.StaticText(form_panel, label="Level:")
        lvl_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        form_sizer.Add(lvl_label, 0, wx.LEFT, 15)

        levels = ['easy', 'medium', 'hard']
        self.level_choice = wx.Choice(form_panel, choices=levels, size=(250, 30))
        self.level_choice.SetSelection(0)  # Default to first option
        form_sizer.Add(self.level_choice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        form_panel.SetSizer(form_sizer)
        vbox.Add(form_panel, 0, wx.EXPAND | wx.ALL, 10)

        # Upload button
        btn_upload = wx.Button(panel, label="📤 Upload Video", size=(250, 45))
        btn_upload.SetBackgroundColour(wx.Colour(76, 175, 80))
        btn_upload.SetForegroundColour(wx.WHITE)
        btn_upload.SetFont(btn_font)
        btn_upload.Bind(wx.EVT_BUTTON, self.on_upload)
        vbox.Add(btn_upload, 0, wx.ALIGN_CENTER | wx.ALL, 15)

        # Cancel button
        btn_cancel = wx.Button(panel, label="✖️ Cancel", size=(250, 35))
        btn_cancel.SetBackgroundColour(wx.Colour(108, 117, 125))
        btn_cancel.SetForegroundColour(wx.WHITE)
        btn_cancel.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        vbox.Add(btn_cancel, 0, wx.ALIGN_CENTER | wx.BOTTOM, 15)

        panel.SetSizer(vbox)
        self.Centre()
        self.Show()

    def on_choose_file(self, event):
        """Open file dialog to pick a video file."""
        with wx.FileDialog(
                self,
                "Choose a video file",
                wildcard="Video files (*.mp4;*.mov;*.avi)|*.mp4;*.mov;*.avi",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return

            self.selected_file_path = dialog.GetPath()
            filename = os.path.basename(self.selected_file_path)

            # Get file size
            file_size = os.path.getsize(self.selected_file_path)
            size_mb = file_size / (1024 * 1024)

            self.file_label.SetLabel(f"✅ Selected: {filename} ({size_mb:.1f} MB)")
            self.file_label.SetForegroundColour(wx.Colour(0, 150, 0))

    def on_upload(self, event):
        """Upload video by copying file and registering metadata."""

        # Validation
        if not self.selected_file_path:
            wx.MessageBox(
                "Please choose a video file first!",
                "No File Selected",
                wx.OK | wx.ICON_WARNING
            )
            return

        if not os.path.exists(self.selected_file_path):
            wx.MessageBox(
                "The selected file no longer exists!",
                "File Not Found",
                wx.OK | wx.ICON_ERROR
            )
            return

        category = self.category_choice.GetStringSelection()
        level = self.level_choice.GetStringSelection()
        filename = os.path.basename(self.selected_file_path)

        print(f"[DEBUG] Uploading video:")
        print(f"  File: {filename}")
        print(f"  Category: {category}")
        print(f"  Level: {level}")
        print(f"  Uploader: {self.client.username}")

        # Show progress
        wx.BeginBusyCursor()

        try:
            # Step 1: Find the Server/videos folder
            # Get current file location (Client folder)
            client_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"[DEBUG] Client dir: {client_dir}")

            # Go up to project root
            project_root = os.path.dirname(client_dir)
            print(f"[DEBUG] Project root: {project_root}")

            # Videos folder should be in Server/videos
            server_dir = os.path.join(project_root, "Server")
            videos_folder = os.path.join(server_dir, "videos")

            print(f"[DEBUG] Server dir: {server_dir}")
            print(f"[DEBUG] Videos folder: {videos_folder}")

            # Create folder if doesn't exist
            if not os.path.exists(videos_folder):
                os.makedirs(videos_folder)
                print(f"[DEBUG] Created videos folder: {videos_folder}")

            destination = os.path.join(videos_folder, filename)
            print(f"[DEBUG] Destination path: {destination}")

            # Check if file already exists
            if os.path.exists(destination):
                result = wx.MessageBox(
                    f"A video named '{filename}' already exists.\n"
                    "Do you want to overwrite it?",
                    "File Exists",
                    wx.YES_NO | wx.ICON_QUESTION
                )

                if result != wx.YES:
                    wx.EndBusyCursor()
                    return

            print(f"[DEBUG] Copying file to: {destination}")
            shutil.copy2(self.selected_file_path, destination)
            print(f"[DEBUG] File copied successfully!")

            # Step 2: Register metadata in database
            payload = {
                "title": filename,
                "category": category,
                "level": level,
                "uploader": self.client.username
            }

            print(f"[DEBUG] Registering metadata...")
            response = self.client._send_request("ADD_VIDEO", payload)

            wx.EndBusyCursor()

            if response.get("status") == "success":
                wx.MessageBox(
                    f"✅ Video uploaded successfully!\n\n"
                    f"File: {filename}\n"
                    f"Category: {category}\n"
                    f"Level: {level}",
                    "Upload Successful",
                    wx.OK | wx.ICON_INFORMATION
                )
                print(f"[DEBUG] Upload completed successfully!")
                self.Close()
            else:
                error_msg = response.get("message", "Unknown error")
                print(f"[DEBUG] Metadata registration failed: {error_msg}")

                # Check if error is about duplicate title
                if "already exists" in error_msg.lower():
                    # Duplicate title - ask about deleting file
                    result = wx.MessageBox(
                        f"❌ A video with this name already exists in the database!\n\n"
                        f"File '{filename}' was copied to the videos folder,\n"
                        f"but metadata registration failed.\n\n"
                        f"Do you want to delete the copied file?",
                        "Duplicate Video Name",
                        wx.YES_NO | wx.ICON_ERROR
                    )

                    if result == wx.YES:
                        try:
                            os.remove(destination)
                            print(f"[DEBUG] Copied file deleted: {destination}")
                            wx.MessageBox(
                                "File deleted successfully.\n\n"
                                "Please rename your video and try again.",
                                "File Deleted",
                                wx.OK | wx.ICON_INFORMATION
                            )
                        except Exception as del_err:
                            print(f"[DEBUG] Could not delete file: {del_err}")
                            wx.MessageBox(
                                f"Could not delete file:\n{del_err}\n\n"
                                f"Please delete manually: {destination}",
                                "Delete Failed",
                                wx.OK | wx.ICON_ERROR
                            )
                    else:
                        wx.MessageBox(
                            f"File kept at:\n{destination}\n\n"
                            f"You can:\n"
                            f"1. Delete it manually\n"
                            f"2. Rename it and update database\n"
                            f"3. Keep it as backup",
                            "File Kept",
                            wx.OK | wx.ICON_INFORMATION
                        )
                else:
                    # Other error - show generic message
                    result = wx.MessageBox(
                        f"Failed to register video metadata:\n{error_msg}\n\n"
                        f"The file was copied to: {destination}\n\n"
                        f"Do you want to delete the copied file?",
                        "Registration Failed",
                        wx.YES_NO | wx.ICON_ERROR
                    )

                    if result == wx.YES:
                        try:
                            os.remove(destination)
                            print(f"[DEBUG] Copied file deleted")
                        except:
                            pass

        except PermissionError:
            wx.EndBusyCursor()
            wx.MessageBox(
                "Permission denied when copying file.\n"
                "Make sure the videos folder is writable.",
                "Permission Error",
                wx.OK | wx.ICON_ERROR
            )

        except Exception as e:
            wx.EndBusyCursor()
            print(f"[DEBUG] Upload error: {e}")
            import traceback
            traceback.print_exc()

            wx.MessageBox(
                f"Upload failed:\n{str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )