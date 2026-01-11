"""
Gal Haham
GUI window for uploading new videos to the Tennis Social platform.
Handles file selection, metadata input, file copying,
and database registration.
REFACTORED: on_upload method split into focused helper methods.
"""
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

    REFACTORED: Large on_upload method split
    into single-responsibility helpers.
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
            # Step 4: Copy file to server
            destination = self._copy_file_to_server(upload_data)
            if destination is None:
                return

            # Step 5: Register in database
            success = self._register_video_metadata(upload_data)

            # Step 6: Handle result
            if success:
                self._handle_upload_success(upload_data)
            else:
                self._handle_upload_failure(upload_data, destination)

        except PermissionError:
            self._handle_permission_error()
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

    def _copy_file_to_server(self, upload_data):
        """
        Copy video file to server's videos folder.

        Args:
            upload_data: Dict containing upload information

        Returns:
            str: Destination path if successful, None if cancelled
        """
        # Get destination path
        videos_folder = self._get_videos_folder_path()
        destination = os.path.join(videos_folder, upload_data['filename'])

        print(f"[DEBUG] Copying to: {destination}")

        # Check for existing file
        if not self._check_overwrite_permission(
                destination,
                upload_data['filename'],
        ):
            wx.EndBusyCursor()
            return None

        # Copy file
        shutil.copy2(self.selected_file_path, destination)
        print(f"[DEBUG] File copied successfully!")

        return destination

    def _get_videos_folder_path(self):
        """
        Get the path to the server's videos folder.

        Returns:
            str: Path to videos folder
        """
        client_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(client_dir)
        server_dir = os.path.join(project_root, "Server")
        videos_folder = os.path.join(server_dir, "videos")

        # Create folder if doesn't exist
        if not os.path.exists(videos_folder):
            os.makedirs(videos_folder)
            print(f"[DEBUG] Created videos folder: {videos_folder}")

        return videos_folder

    def _check_overwrite_permission(self, destination, filename):
        """
        Check if user wants to overwrite existing file.

        Args:
            destination: Destination file path
            filename: Name of the file

        Returns:
            bool: True if should proceed, False if cancelled
        """
        if os.path.exists(destination):
            result = wx.MessageBox(
                f"A video named '{filename}' already exists.\n"
                "Do you want to overwrite it?",
                "File Exists",
                wx.YES_NO | wx.ICON_QUESTION
            )
            return result == wx.YES

        return True

    def _register_video_metadata(self, upload_data):
        """
        Register video metadata in database.

        Args:
            upload_data: Dict containing upload information

        Returns:
            bool: True if successful, False otherwise
        """
        payload = {
            "title": upload_data['filename'],
            "category": upload_data['category'],
            "level": upload_data['level'],
            "uploader": self.client.username
        }

        print(f"[DEBUG] Registering metadata...")
        response = self.client._send_request("ADD_VIDEO", payload)

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

    def _handle_upload_failure(self, upload_data, destination):
        """
        Handle upload failure (metadata registration failed).

        Args:
            upload_data: Dict containing upload information
            destination: Path where file was copied
        """
        response = self.client._send_request("ADD_VIDEO", {
            "title": upload_data['filename'],
            "category": upload_data['category'],
            "level": upload_data['level'],
            "uploader": self.client.username
        })

        error_msg = response.get("message", "Unknown error")
        print(f"[DEBUG] Metadata registration failed: {error_msg}")

        if "already exists" in error_msg.lower():
            self._handle_duplicate_error(upload_data['filename'], destination)
        else:
            self._handle_generic_registration_error(error_msg, destination)

    def _handle_duplicate_error(self, filename, destination):
        """
        Handle duplicate video name error.

        Args:
            filename: Name of the video file
            destination: Path where file was copied
        """
        result = wx.MessageBox(
            f"A video with this name already exists in the database!\n\n"
            f"File '{filename}' was copied to the videos folder, \n"
            f"but metadata registration failed.\n\n"
            f"Do you want to delete the copied file?",
            "Duplicate Video Name",
            wx.YES_NO | wx.ICON_ERROR
        )

        if result == wx.YES:
            self._delete_copied_file(destination)
        else:
            self._show_file_kept_message(destination)

    def _handle_generic_registration_error(self, error_msg, destination):
        """
        Handle generic registration error.

        Args:
            error_msg: Error message from server
            destination: Path where file was copied
        """
        result = wx.MessageBox(
            f"Failed to register video metadata: \n{error_msg}\n\n"
            f"The file was copied to: {destination}\n\n"
            f"Do you want to delete the copied file?",
            "Registration Failed",
            wx.YES_NO | wx.ICON_ERROR
        )

        if result == wx.YES:
            self._delete_copied_file(destination)

    def _delete_copied_file(self, destination):
        """
        Delete a copied file and show result.

        Args:
            destination: Path to file to delete
        """
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
                f"Could not delete file: \n{del_err}\n\n"
                f"Please delete manually: {destination}",
                "Delete Failed",
                wx.OK | wx.ICON_ERROR
            )

    def _show_file_kept_message(self, destination):
        """
        Show message about kept file options.

        Args:
            destination: Path where file is located
        """
        wx.MessageBox(
            f"File kept at: \n{destination}\n\n"
            f"You can: \n"
            f"1. Delete it manually\n"
            f"2. Rename it and update database\n"
            f"3. Keep it as backup",
            "File Kept",
            wx.OK | wx.ICON_INFORMATION
        )

    def _handle_permission_error(self):
        """Handle permission denied error."""
        wx.MessageBox(
            "Permission denied when copying file.\n"
            "Make sure the videos folder is writable.",
            "Permission Error",
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
