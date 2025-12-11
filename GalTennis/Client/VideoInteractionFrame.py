import wx
import time
from Video_Player_Client import run_video_player_client


class VideoInteractionFrame(wx.Frame):
    """
    Enhanced GUI for video interaction with Likes and Comments.
    Shows video info, like count, and provides easy access to comments.
    """

    def __init__(self, client, video_data, parent_window=None):
        super().__init__(
            parent=None,
            title=f"🎾 {video_data['title']}",
            size=(500, 600)
        )

        self.client = client
        self.video = video_data
        self.parent_window = parent_window  # Reference to calling window
        self.is_liked = False
        self.like_count = 0

        # Set background color
        self.SetBackgroundColour(wx.Colour(245, 245, 245))

        # Bind close event (X button)
        self.Bind(wx.EVT_CLOSE, self.on_close_window)

        self.init_ui()
        self.load_video_stats()
        self.Centre()
        self.Show()

    def init_ui(self):
        """Initialize the user interface"""
        main_panel = wx.Panel(self)
        main_panel.SetBackgroundColour(wx.Colour(245, 245, 245))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # ==================
        # HEADER SECTION
        # ==================
        header_panel = wx.Panel(main_panel)
        header_panel.SetBackgroundColour(wx.Colour(76, 175, 80))
        header_sizer = wx.BoxSizer(wx.VERTICAL)

        # Video title
        title = wx.StaticText(header_panel, label=self.video['title'])
        title.SetForegroundColour(wx.WHITE)
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        header_sizer.Add(title, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        # Video metadata
        metadata_text = f"Category: {self.video.get('category', 'N/A')} | Level: {self.video.get('level', 'N/A')}"
        metadata = wx.StaticText(header_panel, label=metadata_text)
        metadata.SetForegroundColour(wx.Colour(230, 230, 230))
        metadata_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
        metadata.SetFont(metadata_font)
        header_sizer.Add(metadata, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Uploader
        uploader = wx.StaticText(header_panel, label=f"By: {self.video.get('uploader', 'Unknown')}")
        uploader.SetForegroundColour(wx.Colour(230, 230, 230))
        header_sizer.Add(uploader, 0, wx.BOTTOM | wx.ALIGN_CENTER, 10)

        header_panel.SetSizer(header_sizer)
        main_sizer.Add(header_panel, 0, wx.EXPAND)

        # ==================
        # STATS SECTION
        # ==================
        stats_panel = wx.Panel(main_panel)
        stats_panel.SetBackgroundColour(wx.WHITE)
        stats_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Like count
        self.like_icon = wx.StaticText(stats_panel, label="❤️")
        like_font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.like_icon.SetFont(like_font)
        stats_sizer.Add(self.like_icon, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)

        self.like_count_label = wx.StaticText(stats_panel, label="Loading...")
        count_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.like_count_label.SetFont(count_font)
        self.like_count_label.SetForegroundColour(wx.Colour(100, 100, 100))
        stats_sizer.Add(self.like_count_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)

        stats_panel.SetSizer(stats_sizer)
        main_sizer.Add(stats_panel, 0, wx.EXPAND | wx.TOP, 10)

        # ==================
        # ACTIONS SECTION
        # ==================
        actions_panel = wx.Panel(main_panel)
        actions_panel.SetBackgroundColour(wx.Colour(245, 245, 245))
        actions_sizer = wx.BoxSizer(wx.VERTICAL)

        # Play button
        play_btn = wx.Button(actions_panel, label="▶️  Play Video", size=(300, 50))
        play_btn.SetBackgroundColour(wx.Colour(76, 175, 80))
        play_btn.SetForegroundColour(wx.WHITE)
        btn_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        play_btn.SetFont(btn_font)
        play_btn.Bind(wx.EVT_BUTTON, self.on_play)
        actions_sizer.Add(play_btn, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        # Like button
        self.like_btn = wx.Button(actions_panel, label="❤️  Like", size=(300, 45))
        self.like_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.like_btn.SetForegroundColour(wx.Colour(220, 53, 69))
        self.like_btn.SetFont(btn_font)
        self.like_btn.Bind(wx.EVT_BUTTON, self.on_like)
        actions_sizer.Add(self.like_btn, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Comments button
        comments_btn = wx.Button(actions_panel, label="💬  View Comments", size=(300, 45))
        comments_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        comments_btn.SetForegroundColour(wx.Colour(0, 123, 255))
        comments_btn.SetFont(btn_font)
        comments_btn.Bind(wx.EVT_BUTTON, self.on_comments)
        actions_sizer.Add(comments_btn, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Back button
        back_btn = wx.Button(actions_panel, label="⬅️  Back to Videos", size=(300, 40))
        back_btn.SetBackgroundColour(wx.Colour(108, 117, 125))
        back_btn.SetForegroundColour(wx.WHITE)
        back_btn.Bind(wx.EVT_BUTTON, self.on_back)
        actions_sizer.Add(back_btn, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        actions_panel.SetSizer(actions_sizer)
        main_sizer.Add(actions_panel, 1, wx.EXPAND)

        # ==================
        # QUICK COMMENTS PREVIEW
        # ==================
        preview_panel = wx.Panel(main_panel)
        preview_panel.SetBackgroundColour(wx.WHITE)
        preview_sizer = wx.BoxSizer(wx.VERTICAL)

        preview_title = wx.StaticText(preview_panel, label="Recent Comments")
        preview_title_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        preview_title.SetFont(preview_title_font)
        preview_sizer.Add(preview_title, 0, wx.ALL, 10)

        self.comments_preview = wx.TextCtrl(
            preview_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            size=(-1, 150)
        )
        self.comments_preview.SetBackgroundColour(wx.Colour(250, 250, 250))
        preview_sizer.Add(self.comments_preview, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        preview_panel.SetSizer(preview_sizer)
        main_sizer.Add(preview_panel, 0, wx.EXPAND | wx.ALL, 10)

        main_panel.SetSizer(main_sizer)

    def load_video_stats(self):
        """Load like count and recent comments"""
        # Load like count
        try:
            response = self.client._send_request('GET_LIKES_COUNT', {
                'title': self.video['title']
            })

            if response.get('status') == 'success':
                self.like_count = response.get('count', 0)
                self.update_like_display()
        except Exception as e:
            print(f"Error loading likes: {e}")

        # Load recent comments
        self.load_comments_preview()

    def update_like_display(self):
        """Update the like count display"""
        likes_text = f"{self.like_count} {'Like' if self.like_count == 1 else 'Likes'}"
        self.like_count_label.SetLabel(likes_text)

        # Update button appearance based on like status
        if self.is_liked:
            self.like_btn.SetLabel("💔  Unlike")
            self.like_btn.SetBackgroundColour(wx.Colour(220, 53, 69))
            self.like_btn.SetForegroundColour(wx.WHITE)
        else:
            self.like_btn.SetLabel("❤️  Like")
            self.like_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.like_btn.SetForegroundColour(wx.Colour(220, 53, 69))

    def load_comments_preview(self):
        """Load and display recent comments"""
        try:
            print(f"[DEBUG Preview] Loading comments for: {self.video['title']}")

            response = self.client._send_request('GET_COMMENTS', {
                'video_title': self.video['title']
            })

            print(f"[DEBUG Preview] Response: {response}")

            if response.get('status') == 'success':
                comments = response.get('comments', [])

                print(f"[DEBUG Preview] Found {len(comments)} comments")

                if comments:
                    # Show last 3 comments
                    preview_text = ""
                    for comment in comments[-3:]:
                        preview_text += f"👤 {comment['username']}: {comment['content']}\n"
                        preview_text += f"   ({comment['timestamp']})\n\n"

                    self.comments_preview.SetValue(preview_text.strip())
                else:
                    self.comments_preview.SetValue("No comments yet. Be the first to comment!")
        except Exception as e:
            print(f"[DEBUG Preview] Error: {e}")
            import traceback
            traceback.print_exc()
            self.comments_preview.SetValue("Unable to load comments.")

    def on_play(self, event):
        """Play the video"""
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
                f"Failed to play video: {response.get('message', 'Unknown error')}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )

    def on_like(self, event):
        """Toggle like status"""
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
            msg = "❤️ Liked!" if self.is_liked else "💔 Unliked"
            wx.MessageBox(msg, "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox(
                f"Action failed: {response.get('message', 'Unknown error')}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )

    def on_comments(self, event):
        """Open full comments window"""
        CommentsFrame(self.client, self.video, self)

    def on_back(self, event):
        """Close this window and return to grid"""
        self.Close()

        # If we have a parent window, show it again
        if self.parent_window:
            self.parent_window.Show()

    def on_close_window(self, event):
        """Handle window close event (X button)"""
        # Show parent window before closing
        if self.parent_window:
            self.parent_window.Show()

        # Continue with normal close
        event.Skip()


class CommentsFrame(wx.Frame):
    """
    Full comments window with ability to view all comments
    and add new ones.
    """

    def __init__(self, client, video_data, parent_frame):
        super().__init__(
            parent=None,
            title=f"💬 Comments - {video_data['title']}",
            size=(600, 500)
        )

        self.client = client
        self.video = video_data
        self.parent_frame = parent_frame

        self.SetBackgroundColour(wx.Colour(245, 245, 245))

        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close_window)

        self.init_ui()
        self.load_comments()
        self.Centre()
        self.Show()

    def init_ui(self):
        """Initialize comments UI"""
        main_panel = wx.Panel(self)
        main_panel.SetBackgroundColour(wx.Colour(245, 245, 245))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header_panel = wx.Panel(main_panel)
        header_panel.SetBackgroundColour(wx.Colour(0, 123, 255))
        header_sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(header_panel, label="💬 Comments")
        title.SetForegroundColour(wx.WHITE)
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        header_sizer.Add(title, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        video_name = wx.StaticText(header_panel, label=self.video['title'])
        video_name.SetForegroundColour(wx.Colour(230, 230, 230))
        header_sizer.Add(video_name, 0, wx.BOTTOM | wx.ALIGN_CENTER, 10)

        header_panel.SetSizer(header_sizer)
        main_sizer.Add(header_panel, 0, wx.EXPAND)

        # Comments display area
        self.comments_display = wx.TextCtrl(
            main_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            size=(-1, 300)
        )
        self.comments_display.SetBackgroundColour(wx.WHITE)
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.comments_display.SetFont(font)
        main_sizer.Add(self.comments_display, 1, wx.EXPAND | wx.ALL, 10)

        # Add comment section
        add_comment_panel = wx.Panel(main_panel)
        add_comment_panel.SetBackgroundColour(wx.Colour(245, 245, 245))
        add_sizer = wx.BoxSizer(wx.HORIZONTAL)

        add_label = wx.StaticText(add_comment_panel, label="Add comment:")
        add_sizer.Add(add_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        self.comment_input = wx.TextCtrl(
            add_comment_panel,
            size=(350, 30),
            style=wx.TE_PROCESS_ENTER  # Enable Enter key event
        )
        self.comment_input.Bind(wx.EVT_TEXT_ENTER, self.on_add_comment)
        add_sizer.Add(self.comment_input, 1, wx.EXPAND | wx.RIGHT, 10)

        add_btn = wx.Button(add_comment_panel, label="📤 Post", size=(80, 30))
        add_btn.SetBackgroundColour(wx.Colour(0, 123, 255))
        add_btn.SetForegroundColour(wx.WHITE)
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_comment)
        add_sizer.Add(add_btn, 0)

        add_comment_panel.SetSizer(add_sizer)
        main_sizer.Add(add_comment_panel, 0, wx.EXPAND | wx.ALL, 10)

        # Bottom buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        refresh_btn = wx.Button(main_panel, label="🔄 Refresh", size=(120, 35))
        refresh_btn.Bind(wx.EVT_BUTTON, lambda e: self.load_comments())
        button_sizer.Add(refresh_btn, 0, wx.RIGHT, 10)

        close_btn = wx.Button(main_panel, label="✖️ Close", size=(120, 35))
        close_btn.SetBackgroundColour(wx.Colour(108, 117, 125))
        close_btn.SetForegroundColour(wx.WHITE)
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        button_sizer.Add(close_btn, 0)

        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 15)

        main_panel.SetSizer(main_sizer)

    def load_comments(self):
        """Load and display all comments"""
        try:
            print(f"[DEBUG] Loading comments for: {self.video['title']}")

            response = self.client._send_request('GET_COMMENTS', {
                'video_title': self.video['title']
            })

            print(f"[DEBUG] Server response: {response}")

            if response.get('status') == 'success':
                comments = response.get('comments', [])

                print(f"[DEBUG] Found {len(comments)} comments")

                if comments:
                    display_text = ""
                    for i, comment in enumerate(comments, 1):
                        display_text += f"{'=' * 50}\n"
                        display_text += f"👤 {comment['username']}\n"
                        display_text += f"📅 {comment['timestamp']}\n"
                        display_text += f"💬 {comment['content']}\n"

                    display_text += f"{'=' * 50}\n"
                    display_text += f"\nTotal: {len(comments)} comment(s)"

                    self.comments_display.SetValue(display_text)
                else:
                    self.comments_display.SetValue("No comments yet.\nBe the first to share your thoughts!")
            else:
                error_msg = response.get('message', 'Unable to load comments')
                print(f"[DEBUG] Error from server: {error_msg}")
                self.comments_display.SetValue(f"Error: {error_msg}")

        except Exception as e:
            print(f"[DEBUG] Exception loading comments: {e}")
            import traceback
            traceback.print_exc()
            self.comments_display.SetValue(f"Error loading comments: {str(e)}")

    def on_add_comment(self, event):
        """Add a new comment"""
        comment_text = self.comment_input.GetValue().strip()

        if not comment_text:
            wx.MessageBox("Please enter a comment!", "Warning", wx.OK | wx.ICON_WARNING)
            return

        print(f"[DEBUG] Adding comment: '{comment_text}'")
        print(f"[DEBUG] Video: {self.video['title']}")
        print(f"[DEBUG] Username: {self.client.username}")

        # Send comment to server
        response = self.client._send_request('ADD_COMMENT', {
            'username': self.client.username,
            'video_title': self.video['title'],
            'content': comment_text
        })

        print(f"[DEBUG] Add comment response: {response}")

        if response.get('status') == 'success':
            wx.MessageBox("✅ Comment posted!", "Success", wx.OK | wx.ICON_INFORMATION)
            self.comment_input.Clear()
            self.load_comments()

            # Update parent frame's preview
            if self.parent_frame:
                self.parent_frame.load_comments_preview()
        else:
            error_msg = response.get('message', 'Unknown error')
            print(f"[DEBUG] Failed to add comment: {error_msg}")
            wx.MessageBox(
                f"Failed to post comment: {error_msg}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )

    def on_close_window(self, event):
        """Handle window close event (X button)"""
        # Parent frame doesn't need to be shown - it's already visible
        # Just close this window
        event.Skip()