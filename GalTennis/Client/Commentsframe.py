"""
Gal Haham
Full comments window for viewing and adding video comments.
Separated from VideoInteractionFrame for better code organization.
"""
import wx

# Window Size
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 500

# Colors - RGB Values
COLOR_BG_R = 245
COLOR_BG_G = 245
COLOR_BG_B = 245
COLOR_HEADER_R = 0
COLOR_HEADER_G = 123
COLOR_HEADER_B = 255
COLOR_TEXT_LIGHT_R = 230
COLOR_TEXT_LIGHT_G = 230
COLOR_TEXT_LIGHT_B = 230
COLOR_BUTTON_CLOSE_R = 108
COLOR_BUTTON_CLOSE_G = 117
COLOR_BUTTON_CLOSE_B = 125

# Colors
COLOR_BACKGROUND = wx.Colour(COLOR_BG_R, COLOR_BG_G, COLOR_BG_B)
COLOR_HEADER = wx.Colour(COLOR_HEADER_R, COLOR_HEADER_G, COLOR_HEADER_B)
COLOR_WHITE = wx.WHITE
COLOR_TEXT_LIGHT = wx.Colour(
    COLOR_TEXT_LIGHT_R,
    COLOR_TEXT_LIGHT_G,
    COLOR_TEXT_LIGHT_B,
)
COLOR_BUTTON_CLOSE = wx.Colour(
    COLOR_BUTTON_CLOSE_R,
    COLOR_BUTTON_CLOSE_G,
    COLOR_BUTTON_CLOSE_B,
)


# Fonts
FONT_SIZE_TITLE = 16
FONT_SIZE_NORMAL = 10

# Spacing
SPACING_HEADER_ALL = 15
SPACING_HEADER_BOTTOM = 10
SPACING_DISPLAY = 10
SPACING_INPUT_RIGHT = 10
SPACING_BUTTON_RIGHT = 10
SPACING_BUTTON_BOTTOM = 15

# Widget Sizes
COMMENTS_DISPLAY_HEIGHT = 300
COMMENT_INPUT_WIDTH = 350
COMMENT_INPUT_HEIGHT = 30
POST_BUTTON_WIDTH = 80
POST_BUTTON_HEIGHT = 30
ACTION_BUTTON_WIDTH = 120
ACTION_BUTTON_HEIGHT = 35

# Comment Display
SEPARATOR_LENGTH = 50
COMMENT_START_INDEX = 1

# Sizer Flags
SIZER_FLAG_PROPORTION_NONE = 0
SIZER_FLAG_PROPORTION_EXPAND = 1
SIZER_FLAG_EXPAND = wx.EXPAND
SIZER_FLAG_DYNAMIC_WIDTH = -1

# Messages
MSG_NO_COMMENTS = "No comments yet.\nBe the first to share your thoughts!"
MSG_ERROR_PREFIX = "Error: "
MSG_EMPTY_COMMENT_WARNING = "Please enter a comment!"
MSG_COMMENT_SUCCESS = "Comment posted!"
MSG_COMMENT_ERROR_PREFIX = "Failed to post comment: "

# Dialog Titles
DIALOG_TITLE_WARNING = "Warning"
DIALOG_TITLE_SUCCESS = "Success"
DIALOG_TITLE_ERROR = "Error"

# Default Values
DEFAULT_ERROR_MESSAGE = "Unknown error"
DEFAULT_LOAD_ERROR_MESSAGE = "Unable to load comments"


class CommentsFrame(wx.Frame):
    """
    Full comments window with ability to view all comments and add new ones.

    Features:
    - Display all comments for a video
    - Add new comments
    - Refresh comments
    - Navigate back to parent frame
    """

    def __init__(self, client, video_data, parent_frame):
        """
        Initialize the comments frame.

        Args:
            client: Client instance for server communication
            video_data: Dict containing video information
            parent_frame: Reference to VideoInteractionFrame
        """
        super().__init__(
            parent=None,
            title=f"Comments - {video_data['title']}",
            size=(WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        self.client = client
        self.video = video_data
        self.parent_frame = parent_frame

        self.SetBackgroundColour(COLOR_BACKGROUND)
        self.Bind(wx.EVT_CLOSE, self.on_close_window)

        self.init_ui()
        self.load_comments()

        self.Centre()
        self.Show()

    def init_ui(self):
        """Initialize comments UI - REFACTORED."""
        main_panel = wx.Panel(self)
        main_panel.SetBackgroundColour(COLOR_BACKGROUND)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self._add_header(main_panel, main_sizer)
        self._add_comments_display(main_panel, main_sizer)
        self._add_comment_input(main_panel, main_sizer)
        self._add_action_buttons(main_panel, main_sizer)

        main_panel.SetSizer(main_sizer)

    def _add_header(self, main_panel, main_sizer):
        """Add header section with title."""
        header_panel = wx.Panel(main_panel)
        header_panel.SetBackgroundColour(COLOR_HEADER)
        header_sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(header_panel, label="Comments")
        title.SetForegroundColour(COLOR_WHITE)
        title_font = wx.Font(
            FONT_SIZE_TITLE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title.SetFont(title_font)
        header_sizer.Add(
            title,
            SIZER_FLAG_PROPORTION_NONE,
            wx.ALL | wx.ALIGN_CENTER,
            SPACING_HEADER_ALL,
        )
        # Video name
        video_name = wx.StaticText(header_panel, label=self.video['title'])
        video_name.SetForegroundColour(COLOR_TEXT_LIGHT)
        header_sizer.Add(
            video_name,
            SIZER_FLAG_PROPORTION_NONE,
            wx.BOTTOM | wx.ALIGN_CENTER,
            SPACING_HEADER_BOTTOM,
        )
        header_panel.SetSizer(header_sizer)
        main_sizer.Add(
            header_panel,
            SIZER_FLAG_PROPORTION_NONE,
            SIZER_FLAG_EXPAND,
        )

    def _add_comments_display(self, main_panel, main_sizer):
        """Add comments display area."""
        self.comments_display = wx.TextCtrl(
            main_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            size=(SIZER_FLAG_DYNAMIC_WIDTH, COMMENTS_DISPLAY_HEIGHT)
        )
        self.comments_display.SetBackgroundColour(COLOR_WHITE)
        font = wx.Font(
            FONT_SIZE_NORMAL,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.comments_display.SetFont(font)
        main_sizer.Add(
            self.comments_display,
            SIZER_FLAG_PROPORTION_EXPAND,
            SIZER_FLAG_EXPAND | wx.ALL,
            SPACING_DISPLAY,
        )

    def _add_comment_input(self, main_panel, main_sizer):
        """Add comment input section."""
        add_comment_panel = wx.Panel(main_panel)
        add_comment_panel.SetBackgroundColour(COLOR_BACKGROUND)
        add_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Label
        add_label = wx.StaticText(add_comment_panel, label="Add comment:")
        add_sizer.Add(
            add_label,
            SIZER_FLAG_PROPORTION_NONE,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            SPACING_INPUT_RIGHT,
        )
        # Input field
        self.comment_input = wx.TextCtrl(
            add_comment_panel,
            size=(COMMENT_INPUT_WIDTH, COMMENT_INPUT_HEIGHT),
            style=wx.TE_PROCESS_ENTER
        )
        self.comment_input.Bind(wx.EVT_TEXT_ENTER, self.on_add_comment)
        add_sizer.Add(
            self.comment_input,
            SIZER_FLAG_PROPORTION_EXPAND,
            SIZER_FLAG_EXPAND | wx.RIGHT,
            SPACING_INPUT_RIGHT,
        )
        # Post button
        add_btn = wx.Button(
            add_comment_panel,
            label="Post",
            size=(POST_BUTTON_WIDTH, POST_BUTTON_HEIGHT)
        )
        add_btn.SetBackgroundColour(COLOR_HEADER)
        add_btn.SetForegroundColour(COLOR_WHITE)
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_comment)
        add_sizer.Add(add_btn, SIZER_FLAG_PROPORTION_NONE)

        add_comment_panel.SetSizer(add_sizer)
        main_sizer.Add(
            add_comment_panel,
            SIZER_FLAG_PROPORTION_NONE,
            SIZER_FLAG_EXPAND | wx.ALL,
            SPACING_DISPLAY,
        )

    def _add_action_buttons(self, main_panel, main_sizer):
        """Add action buttons (refresh, close)."""
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Refresh button
        refresh_btn = wx.Button(
            main_panel,
            label="Refresh",
            size=(ACTION_BUTTON_WIDTH, ACTION_BUTTON_HEIGHT)
        )
        refresh_btn.Bind(wx.EVT_BUTTON, lambda e: self.load_comments())
        button_sizer.Add(
            refresh_btn,
            SIZER_FLAG_PROPORTION_NONE,
            wx.RIGHT,
            SPACING_BUTTON_RIGHT,
        )
        # Close button
        close_btn = wx.Button(
            main_panel,
            label="Close",
            size=(ACTION_BUTTON_WIDTH, ACTION_BUTTON_HEIGHT)
        )
        close_btn.SetBackgroundColour(COLOR_BUTTON_CLOSE)
        close_btn.SetForegroundColour(COLOR_WHITE)
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        button_sizer.Add(close_btn, SIZER_FLAG_PROPORTION_NONE)

        main_sizer.Add(
            button_sizer,
            SIZER_FLAG_PROPORTION_NONE,
            wx.ALIGN_CENTER | wx.BOTTOM,
            SPACING_BUTTON_BOTTOM,
        )

    def load_comments(self):
        """Load and display all comments from server - REFACTORED."""
        try:
            print(f"[DEBUG] Loading comments for: {self.video['title']}")

            response = self._request_comments_from_server()
            self._process_comments_response(response)

        except Exception as e:
            self._handle_comments_load_error(e)

    def _request_comments_from_server(self):
        """
        Request comments from server.

        Returns:
            dict: Server response
        """
        response = self.client._send_request('GET_COMMENTS', {
            'video_title': self.video['title']
        })
        print(f"[DEBUG] Server response: {response}")
        return response

    def _process_comments_response(self, response):
        """
        Process server response and display comments.
        """
        if response.get('status') == 'success':
            comments = response.get('comments', [])
            print(f"[DEBUG] Found {len(comments)} comments")

            if comments:
                self._display_comments(comments)
            else:
                self.comments_display.SetValue(MSG_NO_COMMENTS)
        else:
            error_msg = response.get('message', DEFAULT_LOAD_ERROR_MESSAGE)
            print(f"[DEBUG] Error from server: {error_msg}")
            self.comments_display.SetValue(f"{MSG_ERROR_PREFIX}{error_msg}")

    def _handle_comments_load_error(self, exception):
        """
        Handle error during comments loading.

        Args:
            exception: Exception that occurred
        """
        print(f"[DEBUG] Exception loading comments: {exception}")
        import traceback
        traceback.print_exc()
        self.comments_display.SetValue(
            f"Error loading comments: {str(exception)}"
        )

    def _display_comments(self, comments):
        """
        Format and display comments.

        Args:
            comments: List of comment dictionaries
        """
        display_text = ""
        for i, comment in enumerate(comments, COMMENT_START_INDEX):
            display_text += f"{'=' * SEPARATOR_LENGTH}\n"
            display_text += f"{comment['username']}\n"
            display_text += f"{comment['timestamp']}\n"
            display_text += f"{comment['content']}\n"

        display_text += f"{'=' * SEPARATOR_LENGTH}\n"
        display_text += f"\nTotal: {len(comments)} comment(s)"

        self.comments_display.SetValue(display_text)

    def on_add_comment(self, event):
        """
        Add a new comment.

        Args:
            event: wx.Event
        """
        comment_text = self.comment_input.GetValue().strip()

        if not comment_text:
            wx.MessageBox(
                MSG_EMPTY_COMMENT_WARNING,
                DIALOG_TITLE_WARNING,
                wx.OK | wx.ICON_WARNING
            )
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
            self._handle_comment_added()
        else:
            self._handle_comment_error(response)

    def _handle_comment_added(self):
        """Handle successful comment addition."""
        wx.MessageBox(
            MSG_COMMENT_SUCCESS,
            DIALOG_TITLE_SUCCESS,
            wx.OK | wx.ICON_INFORMATION
        )
        self.comment_input.Clear()
        self.load_comments()

        # Update parent frame's preview
        if self.parent_frame:
            self.parent_frame.load_comments_preview()

    def _handle_comment_error(self, response):
        """
        Handle comment addition error.

        Args:
            response: Server response dict
        """
        error_msg = response.get('message', DEFAULT_ERROR_MESSAGE)
        print(f"Failed to add comment: {error_msg}")
        wx.MessageBox(
            f"{MSG_COMMENT_ERROR_PREFIX}{error_msg}",
            DIALOG_TITLE_ERROR,
            wx.OK | wx.ICON_ERROR
        )

    def on_close_window(self, event):
        """
        Handle window close event

        Args:
            event: wx.CloseEvent
        """
        # Parent frame doesn't need to be shown - it's already visible
        # Just close this window
        event.Skip()
