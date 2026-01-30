"""
Gal Haham
Enhanced GUI for video interaction with Likes and Comments.
Shows video info, like count, and provides easy access to comments.
REFACTORED: init_ui split into focused helper methods, better organization.
"""
import wx
import time
from Video_Player_Client import run_video_player_client


class VideoInteractionFrame(wx.Frame):
    """
    Enhanced GUI for video interaction with Likes and Comments.

    Features:
    - Video information display
    - Play video functionality
    - Like/unlike videos
    - View and add comments
    - Comment preview
    """

    def __init__(self, client, video_data, parent_window=None):
        """
        Initialize the video interaction frame.

        Args:
            client: Client instance for server communication
            video_data: Dict containing video information
            parent_window: Reference to parent window (optional)
        """
        super().__init__(
            parent=None,
            title=f"{video_data['title']}",
            size=(500, 600)
        )

        # Store references
        self.client = client
        self.video = video_data
        self.parent_window = parent_window

        # Initialize state
        self.is_liked = False
        self.like_count = 0

        # Setup UI
        self.SetBackgroundColour(wx.Colour(245, 245, 245))
        self.Bind(wx.EVT_CLOSE, self.on_close_window)

        # Build interface
        self.init_ui()
        self.load_video_stats()

        self.Centre()
        self.Show()

    def init_ui(self):
        """Initialize the user interface - REFACTORED."""
        main_panel = wx.Panel(self)
        main_panel.SetBackgroundColour(wx.Colour(245, 245, 245))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Add UI sections
        self._add_header_section(main_panel, main_sizer)
        self._add_stats_section(main_panel, main_sizer)
        self._add_actions_section(main_panel, main_sizer)
        self._add_comments_preview_section(main_panel, main_sizer)

        main_panel.SetSizer(main_sizer)

    def _add_header_section(self, main_panel, main_sizer):
        """Add header section with video title and metadata."""
        header_panel = wx.Panel(main_panel)
        header_panel.SetBackgroundColour(wx.Colour(76, 175, 80))
        header_sizer = wx.BoxSizer(wx.VERTICAL)

        # Video title
        title = wx.StaticText(header_panel, label=self.video['title'])
        title.SetForegroundColour(wx.WHITE)
        title_font = wx.Font(
            16,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD,
        )
        title.SetFont(title_font)
        header_sizer.Add(title, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        # Video metadata
        metadata_text = (
            f"Category: {self.video.get('category', 'N/A')} | "
            f"Level: {self.video.get('level', 'N/A')}"
        )
        metadata = wx.StaticText(header_panel, label=metadata_text)
        metadata.SetForegroundColour(wx.Colour(230, 230, 230))
        metadata_font = wx.Font(
            10,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_ITALIC,
            wx.FONTWEIGHT_NORMAL,
        )
        metadata.SetFont(metadata_font)
        header_sizer.Add(metadata, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Uploader
        uploader = wx.StaticText(
            header_panel,
            label=f"By: {self.video.get('uploader', 'Unknown')}",
        )
        uploader.SetForegroundColour(wx.Colour(230, 230, 230))
        header_sizer.Add(uploader, 0, wx.BOTTOM | wx.ALIGN_CENTER, 10)

        header_panel.SetSizer(header_sizer)
        main_sizer.Add(header_panel, 0, wx.EXPAND)

    def _add_stats_section(self, main_panel, main_sizer):
        """Add stats section with like count."""
        stats_panel = wx.Panel(main_panel)
        stats_panel.SetBackgroundColour(wx.WHITE)
        stats_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Like icon
        self.like_icon = wx.StaticText(stats_panel, label="")
        like_font = wx.Font(
            24,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
        )
        self.like_icon.SetFont(like_font)
        stats_sizer.Add(
            self.like_icon,
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            10,
        )
        # Like count
        self.like_count_label = wx.StaticText(stats_panel, label="Loading...")
        count_font = wx.Font(
            14,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD,
        )
        self.like_count_label.SetFont(count_font)
        self.like_count_label.SetForegroundColour(wx.Colour(100, 100, 100))
        stats_sizer.Add(
            self.like_count_label,
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            10,
        )
        stats_panel.SetSizer(stats_sizer)
        main_sizer.Add(stats_panel, 0, wx.EXPAND | wx.TOP, 10)

    def _add_actions_section(self, main_panel, main_sizer):
        """Add actions section with buttons."""
        actions_panel = wx.Panel(main_panel)
        actions_panel.SetBackgroundColour(wx.Colour(245, 245, 245))
        actions_sizer = wx.BoxSizer(wx.VERTICAL)

        btn_font = wx.Font(
            12,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD,
        )
        # Play button
        play_btn = self._create_play_button(actions_panel, btn_font)
        actions_sizer.Add(play_btn, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        # Like button
        self.like_btn = self._create_like_button(actions_panel, btn_font)
        actions_sizer.Add(self.like_btn, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Comments button
        comments_btn = self._create_comments_button(actions_panel, btn_font)
        actions_sizer.Add(comments_btn, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Back button
        back_btn = self._create_back_button(actions_panel)
        actions_sizer.Add(back_btn, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        actions_panel.SetSizer(actions_sizer)
        main_sizer.Add(actions_panel, 1, wx.EXPAND)

    def _create_play_button(self, parent, font):
        """Create play video button."""
        btn = wx.Button(parent, label="Play Video", size=(300, 50))
        btn.SetBackgroundColour(wx.Colour(76, 175, 80))
        btn.SetForegroundColour(wx.WHITE)
        btn.SetFont(font)
        btn.Bind(wx.EVT_BUTTON, self.on_play)
        return btn

    def _create_like_button(self, parent, font):
        """Create like/unlike button."""
        btn = wx.Button(parent, label="Like", size=(300, 45))
        btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        btn.SetForegroundColour(wx.Colour(220, 53, 69))
        btn.SetFont(font)
        btn.Bind(wx.EVT_BUTTON, self.on_like)
        return btn

    def _create_comments_button(self, parent, font):
        """Create view comments button."""
        btn = wx.Button(parent, label="View Comments", size=(300, 45))
        btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        btn.SetForegroundColour(wx.Colour(0, 123, 255))
        btn.SetFont(font)
        btn.Bind(wx.EVT_BUTTON, self.on_comments)
        return btn

    def _create_back_button(self, parent):
        """Create back button."""
        btn = wx.Button(parent, label="Back to Videos", size=(300, 40))
        btn.SetBackgroundColour(wx.Colour(108, 117, 125))
        btn.SetForegroundColour(wx.WHITE)
        btn.Bind(wx.EVT_BUTTON, self.on_back)
        return btn

    def _add_comments_preview_section(self, main_panel, main_sizer):
        """Add comments preview section."""
        preview_panel = wx.Panel(main_panel)
        preview_panel.SetBackgroundColour(wx.WHITE)
        preview_sizer = wx.BoxSizer(wx.VERTICAL)

        # Preview title
        preview_title = wx.StaticText(preview_panel, label="Recent Comments")
        preview_title_font = wx.Font(
            11,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD,
        )
        preview_title.SetFont(preview_title_font)
        preview_sizer.Add(preview_title, 0, wx.ALL, 10)

        # Comments preview text control
        self.comments_preview = wx.TextCtrl(
            preview_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            size=(-1, 150)
        )
        self.comments_preview.SetBackgroundColour(wx.Colour(250, 250, 250))
        preview_sizer.Add(
            self.comments_preview,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            10,
        )
        preview_panel.SetSizer(preview_sizer)
        main_sizer.Add(preview_panel, 0, wx.EXPAND | wx.ALL, 10)

    def load_video_stats(self):
        """Load like count and recent comments."""
        self._load_like_count()
        self.load_comments_preview()

    def _load_like_count(self):
        """Load like count from server."""
        try:
            response = self.client._send_request('GET_LIKES_COUNT', {
                'title': self.video['title']
            })

            if response.get('status') == 'success':
                self.like_count = response.get('count', 0)
                self.update_like_display()
        except Exception as e:
            print(f"Error loading likes: {e}")

    def update_like_display(self):
        """Update the like count display and button appearance."""
        # Update count text
        likes_text = (
            f"{self.like_count} "
            f"{'Like' if self.like_count == 1 else 'Likes'}"
        )
        self.like_count_label.SetLabel(likes_text)

        # Update button appearance
        if self.is_liked:
            self.like_btn.SetLabel("Unlike")
            self.like_btn.SetBackgroundColour(wx.Colour(220, 53, 69))
            self.like_btn.SetForegroundColour(wx.WHITE)
        else:
            self.like_btn.SetLabel("Like")
            self.like_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.like_btn.SetForegroundColour(wx.Colour(220, 53, 69))

    def load_comments_preview(self):
        """Load and display recent comments."""
        try:
            print(
                f"[DEBUG Preview] Loading comments for: "
                f"{self.video['title']}"
            )
            response = self.client._send_request('GET_COMMENTS', {
                'video_title': self.video['title']
            })

            print(f"[DEBUG Preview] Response: {response}")

            if response.get('status') == 'success':
                comments = response.get('comments', [])
                print(f"[DEBUG Preview] Found {len(comments)} comments")

                if comments:
                    self._display_comment_preview(comments)
                else:
                    self.comments_preview.SetValue(
                        "No comments yet. Be the first to comment!"
                    )
        except Exception as e:
            print(f"[DEBUG Preview] Error: {e}")
            import traceback
            traceback.print_exc()
            self.comments_preview.SetValue("Unable to load comments.")

    def _display_comment_preview(self, comments):
        """
        Display last 3 comments in preview.

        Args:
            comments: List of comment dictionaries
        """
        preview_text = ""
        for comment in comments[-3:]:
            preview_text += (
                f"{comment['username']}: {comment['content']}\n"
            )
            preview_text += f"   ({comment['timestamp']})\n\n"

        self.comments_preview.SetValue(preview_text.strip())

    def on_play(self, event):
        """
        Play the video.

        Args:
            event: wx.Event
        """
        print(f"Playing video: {self.video['title']}")

        # Request server to start streaming
        response = self.client._send_request('PLAY_VIDEO', {
            'video_title': self.video['title']
        })

        if response.get('status') == 'success':
            time.sleep(2)  # Wait for server to start
            run_video_player_client()
        else:
            wx.MessageBox(
                f"Failed to play video: "
                f"{response.get('message', 'Unknown error')}",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

    def on_like(self, event):
        """
        Toggle like status for this video.

        Args:
            event: wx.Event
        """
        response = self.client._send_request('LIKE_VIDEO', {
            'username': self.client.username,
            'title': self.video['title']
        })

        if response.get('status') == 'success':
            # Toggle local state
            self.is_liked = response.get('is_liked', not self.is_liked)

            # Update count
            if self.is_liked:
                self.like_count += 1
            else:
                self.like_count = max(0, self.like_count - 1)

            self.update_like_display()

            # Show feedback
            msg = "Liked!" if self.is_liked else "Unliked"
            wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox(
                f"Action failed: {response.get('message', 'Unknown error')}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )

    def on_comments(self, event):
        """
        Open full comments window.

        Args:
            event: wx.Event
        """
        from Commentsframe import CommentsFrame
        CommentsFrame(self.client, self.video, self)

    def on_back(self, event):
        """
        Close this window and return to video grid.

        Args:
            event: wx.Event
        """
        self.Close()

        # Show parent window if it exists
        if self.parent_window:
            self.parent_window.Show()

    def on_close_window(self, event):
        """
        Handle window close event (X button).

        Args:
            event: wx.CloseEvent
        """
        # Show parent window before closing
        if self.parent_window:
            self.parent_window.Show()

        # Continue with normal close
        event.Skip()