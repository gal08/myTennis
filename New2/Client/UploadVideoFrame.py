"""
Gal Haham
GUI window for uploading new videos to the Tennis Social platform.
Handles file selection, metadata input, file copying,
and database registration.
REFACTORED: on_upload method split into focused helper methods.
"""
import wx
import os
import base64


class UploadVideoFrame(wx.Frame):
    """
    GUI window for uploading a new video.

    Upload Process:
    1. User selects video file from their computer
    2. File is SENT to server over network (base64 encoded)
    3. Server saves file to videos/ folder
    4. Metadata (title, category, level) is saved to database

    FIXED: Works when client and server are on different machines.
    """

    def __init__(self, client):
        """
        Initialize the upload video window.

        Args:
            client: Client instance for server communication
        """
        super().__init__(parent=None, title="Upload Video", size=(550, 450))

        self.client = client
        self.selected_file_path = None

        self.SetBackgroundColour(wx.Colour(245, 245, 245))

        # Build UI
        self._init_ui()

        self.Centre()
        self.Show()

    def _init_ui(self):
        """Build the complete UI layout."""
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(245, 245, 245))
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Add UI components
        self._add_header(panel, vbox)
        self._add_instructions(panel, vbox)
        self._add_file_selection(panel, vbox)
        self._add_metadata_form(panel, vbox)
        self._add_action_buttons(panel, vbox)

        panel.SetSizer(vbox)

    def _add_header(self, panel, sizer):
        """Add header section with title."""
        header_panel = wx.Panel(panel)
        header_panel.SetBackgroundColour(wx.Colour(76, 175, 80))
        header_sizer = wx.BoxSizer(wx.VERTICAL)

        lbl_title = wx.StaticText(header_panel, label="Upload New Video")
        lbl_title.SetForegroundColour(wx.WHITE)
        title_font = wx.Font(
            16,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD,
        )
        lbl_title.SetFont(title_font)
        header_sizer.Add(lbl_title, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        header_panel.SetSizer(header_sizer)
        sizer.Add(header_panel, 0, wx.EXPAND)

    def _add_instructions(self, panel, sizer):
        """Add instructions text."""
        instructions = wx.StaticText(
            panel,
            label="Select a video file and provide details:"
        )
        instructions.SetForegroundColour(wx.Colour(100, 100, 100))
        sizer.Add(instructions, 0, wx.ALL | wx.ALIGN_CENTER, 15)

    def _add_file_selection(self, panel, sizer):
        """Add file selection section."""
        file_panel = wx.Panel(panel)
        file_panel.SetBackgroundColour(wx.WHITE)
        file_sizer = wx.BoxSizer(wx.VERTICAL)

        # Choose button
        btn_choose = wx.Button(
            file_panel,
            label="Choose Video File",
            size=(250, 40),
        )
        btn_choose.SetBackgroundColour(wx.Colour(0, 123, 255))
        btn_choose.SetForegroundColour(wx.WHITE)
        btn_font = wx.Font(
            11,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD,
        )
        btn_choose.SetFont(btn_font)
        btn_choose.Bind(wx.EVT_BUTTON, self.on_choose_file)
        file_sizer.Add(btn_choose, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        # File label
        self.file_label = wx.StaticText(file_panel, label="No file selected")
        self.file_label.SetForegroundColour(wx.Colour(150, 150, 150))
        file_sizer.Add(self.file_label, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        file_panel.SetSizer(file_sizer)
        sizer.Add(file_panel, 0, wx.EXPAND | wx.ALL, 10)

    def _add_metadata_form(self, panel, sizer):
        """Add metadata form (category and level)."""
        form_panel = wx.Panel(panel)
        form_panel.SetBackgroundColour(wx.WHITE)
        form_sizer = wx.BoxSizer(wx.VERTICAL)

        # Category dropdown
        self._add_category_field(form_panel, form_sizer)

        # Level dropdown
        self._add_level_field(form_panel, form_sizer)

        form_panel.SetSizer(form_sizer)
        sizer.Add(form_panel, 0, wx.EXPAND | wx.ALL, 10)

    def _add_category_field(self, panel, sizer):
        """Add category selection dropdown."""
        cat_label = wx.StaticText(panel, label="Category:")
        cat_label.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
            )
        )
        sizer.Add(cat_label, 0, wx.LEFT | wx.TOP, 15)

        categories = [
            'forehand',
            'backhand',
            'serve',
            'slice',
            'volley',
            'smash',
        ]
        self.category_choice = wx.Choice(
            panel,
            choices=categories,
            size=(250, 30),
        )
        self.category_choice.SetSelection(0)
        sizer.Add(self.category_choice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

    def _add_level_field(self, panel, sizer):
        """Add difficulty level selection dropdown."""
        lvl_label = wx.StaticText(panel, label="Level:")
        lvl_label.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
            )
        )
        sizer.Add(lvl_label, 0, wx.LEFT, 15)

        levels = ['easy', 'medium', 'hard']
        self.level_choice = wx.Choice(panel, choices=levels, size=(250, 30))
        self.level_choice.SetSelection(0)
        sizer.Add(self.level_choice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

    def _add_action_buttons(self, panel, sizer):
        """Add upload and cancel buttons."""
        btn_font = wx.Font(
            11,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD,
        )
        # Upload button
        btn_upload = wx.Button(panel, label=" Upload Video", size=(250, 45))
        btn_upload.SetBackgroundColour(wx.Colour(76, 175, 80))
        btn_upload.SetForegroundColour(wx.WHITE)
        btn_upload.SetFont(btn_font)
        btn_upload.Bind(wx.EVT_BUTTON, self.on_upload)
        sizer.Add(btn_upload, 0, wx.ALIGN_CENTER | wx.ALL, 15)

        # Cancel button
        btn_cancel = wx.Button(panel, label="Cancel", size=(250, 35))
        btn_cancel.SetBackgroundColour(wx.Colour(108, 117, 125))
        btn_cancel.SetForegroundColour(wx.WHITE)
        btn_cancel.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        sizer.Add(btn_cancel, 0, wx.ALIGN_CENTER | wx.BOTTOM, 15)

    def on_choose_file(self, event):
        """
        Open file dialog to select a video file.

        Args:
            event: wx.Event
        """
        with wx.FileDialog(
                self,
                "Choose a video file",
                wildcard="Video files (*.mp4;*.mov;*.avi)|*.mp4;*.mov;*.avi",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return

            self.selected_file_path = dialog.GetPath()
            self._update_file_label()

    def _update_file_label(self):
        """Update file selection label with filename and size."""
        filename = os.path.basename(self.selected_file_path)
        file_size = os.path.getsize(self.selected_file_path)
        size_mb = file_size / (1024 * 1024)

        self.file_label.SetLabel(f"Selected: {filename} ({size_mb: .1f} MB)")
        self.file_label.SetForegroundColour(wx.Colour(0, 150, 0))

    def on_upload(self, event):
        """
        Handle video upload - REFACTORED into smaller steps.
        FIXED: Now sends file over network instead of local copy.

        Args:
            event: wx.Event
        """
        # Step 1: Validate
        if not self._validate_upload():
            return

        # Step 2: Prepare upload data
        upload_data = self._prepare_upload_data()

        # Step 3: Show progress
        wx.BeginBusyCursor()

        try:
            # Step 4: Read and encode file
            file_content = self._read_file_as_base64()
            if file_content is None:
                wx.EndBusyCursor()
                return

            # Step 5: Send to server
            success = self._upload_to_server(upload_data, file_content)

            # Step 6: Handle result
            if success:
                self._handle_upload_success(upload_data)
            else:
                self._handle_upload_failure()

        except Exception as e:
            self._handle_general_error(e)
        finally:
            wx.EndBusyCursor()

    def _validate_upload(self):
        """
        Validate that file is selected and exists.

        Returns:
            bool: True if validation passes, False otherwise
        """
        if not self.selected_file_path:
            wx.MessageBox(
                "Please choose a video file first!",
                "No File Selected",
                wx.OK | wx.ICON_WARNING
            )
            return False

        if not os.path.exists(self.selected_file_path):
            wx.MessageBox(
                "The selected file no longer exists!",
                "File Not Found",
                wx.OK | wx.ICON_ERROR
            )
            return False

        return True

    def _prepare_upload_data(self):
        """
        Prepare upload data dictionary.

        Returns:
            dict: Upload data containing category, level, filename
        """
        return {
            'category': self.category_choice.GetStringSelection(),
            'level': self.level_choice.GetStringSelection(),
            'filename': os.path.basename(self.selected_file_path)
        }

    def _read_file_as_base64(self):
        """
        Read video file and encode as base64 string.

        Returns:
            str: Base64 encoded file content, or None if error
        """
        try:
            print(f"Reading file: {self.selected_file_path}")
            with open(self.selected_file_path, 'rb') as f:
                file_content = f.read()

            # Encode to base64
            encoded = base64.b64encode(file_content).decode('utf-8')
            print(f"File encoded successfully")
            return encoded

        except Exception as e:
            print(f"Error reading file: {e}")
            wx.MessageBox(
                f"Failed to read video file: \n{str(e)}",
                "Read Error",
                wx.OK | wx.ICON_ERROR
            )
            return None

    def _upload_to_server(self, upload_data, file_content):
        """
        Upload video to server over network.

        Args:
            upload_data: Dict containing upload information
            file_content: Base64 encoded file content

        Returns:
            bool: True if successful, False otherwise
        """
        payload = {
            "title": upload_data['filename'],
            "category": upload_data['category'],
            "level": upload_data['level'],
            "uploader": self.client.username,
            "file_content": file_content
        }

        response = self.client._send_request("UPLOAD_VIDEO", payload)

        return response.get("status") == "success"

    def _handle_upload_success(self, upload_data):
        """
        Handle successful upload.

        Args:
            upload_data: Dict containing upload information
        """
        wx.MessageBox(
            f"Video uploaded successfully!\n\n"
            f"File: {upload_data['filename']}\n"
            f"Category: {upload_data['category']}\n"
            f"Level: {upload_data['level']}",
            "Upload Successful",
            wx.OK | wx.ICON_INFORMATION
        )
        print(f"[DEBUG] Upload completed successfully!")
        self.Close()

    def _handle_upload_failure(self):
        """Handle upload failure."""
        wx.MessageBox(
            "Failed to upload video to server.",
            "Upload Failed",
            wx.OK | wx.ICON_ERROR
        )

    def _handle_general_error(self, error):
        """
        Handle general upload error.

        Args:
            error: Exception that occurred
        """
        print(f"[DEBUG] Upload error: {error}")
        import traceback
        traceback.print_exc()

        wx.MessageBox(
            f"Upload failed: \n{str(error)}",
            "Error",
            wx.OK | wx.ICON_ERROR
        )
