"""
Gal Haham
Stories menu frame - provides options for viewing and posting stories.
Serves as navigation hub for story-related features.
REFACTORED: All magic numbers replaced with constants,
comprehensive documentation.
"""
import wx
from Show_all_stories_in_wx import run as show_all_stories
from Story_camera import StoryCameraFrame


# Window Configuration
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 350
WINDOW_TITLE = "Stories Menu"

# Colors
COLOR_BACKGROUND = wx.Colour(245, 245, 245)
COLOR_TITLE = wx.Colour(40, 120, 80)
COLOR_SUBTITLE = wx.Colour(100, 100, 100)

# Fonts
FONT_SIZE_TITLE = 18

# Button Sizes
BUTTON_WIDTH = 250
BUTTON_HEIGHT = 45

# Spacing
SPACING_TITLE_TOP = 30
SPACING_SUBTITLE_TOP = 5
SPACING_BUTTON_FIRST = 15
SPACING_BUTTON_MIDDLE = 15
SPACING_BUTTON_BACK = 25


class StoriesMenuFrame(wx.Frame):
    """
    GUI menu for Stories functionality.

    Features:
    - Post new story (camera)
    - View all stories
    - Return to main menu

    REFACTORED: All magic numbers replaced with constants.
    """

    def __init__(self, username, client_ref, parent_menu=None):
        """
        Initialize the stories menu frame.

        Args:
            username: Current user's username
            client_ref: Client instance for server communication
            parent_menu: Reference to MainMenuFrame (optional)
        """
        super().__init__(
            parent=None,
            title=WINDOW_TITLE,
            size=(WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        self.username = username
        self.client_ref = client_ref
        self.parent_menu = parent_menu

        self._init_ui()

        self.Centre()
        self.Show()

    def _init_ui(self):
        """Initialize the user interface."""
        panel = wx.Panel(self)
        panel.SetBackgroundColour(COLOR_BACKGROUND)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Title and subtitle
        self._add_header(panel, vbox)

        # Buttons
        self._add_buttons(panel, vbox)

        panel.SetSizer(vbox)

    def _add_header(self, panel, vbox):
        """
        Add header section with title and welcome message.

        Args:
            panel: Parent panel
            vbox: Vertical sizer
        """
        # Title
        title = wx.StaticText(panel, label="Stories")
        title.SetFont(
            wx.Font(
                FONT_SIZE_TITLE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD
            )
        )
        title.SetForegroundColour(COLOR_TITLE)
        vbox.Add(
            title,
            flag=wx.ALIGN_CENTER | wx.TOP,
            border=SPACING_TITLE_TOP,
        )
        # Subtitle
        subtitle = wx.StaticText(panel, label=f"Welcome, {self.username}!")
        subtitle.SetForegroundColour(COLOR_SUBTITLE)
        vbox.Add(
            subtitle,
            flag=wx.ALIGN_CENTER | wx.TOP,
            border=SPACING_SUBTITLE_TOP,
        )

    def _add_buttons(self, panel, vbox):
        """
        Add menu buttons.

        Args:
            panel: Parent panel
            vbox: Vertical sizer
        """
        # Post new story button
        btn_post = wx.Button(
            panel,
            label="Post New Story (Camera)",
            size=(BUTTON_WIDTH, BUTTON_HEIGHT)
        )
        btn_post.Bind(wx.EVT_BUTTON, self.on_post_story)
        vbox.Add(
            btn_post,
            flag=wx.ALIGN_CENTER | wx.TOP,
            border=SPACING_BUTTON_FIRST,
        )
        # View all stories button
        btn_view_all = wx.Button(
            panel,
            label="View All Stories",
            size=(BUTTON_WIDTH, BUTTON_HEIGHT)
        )
        btn_view_all.Bind(wx.EVT_BUTTON, self.on_view_all_stories)
        vbox.Add(
            btn_view_all,
            flag=wx.ALIGN_CENTER | wx.TOP,
            border=SPACING_BUTTON_MIDDLE,
        )
        # Back button
        btn_back = wx.Button(
            panel,
            label="⬅ Back to Main Menu",
            size=(BUTTON_WIDTH, BUTTON_HEIGHT)
        )
        btn_back.Bind(wx.EVT_BUTTON, self.on_back)
        vbox.Add(
            btn_back,
            flag=wx.ALIGN_CENTER | wx.TOP,
            border=SPACING_BUTTON_BACK,
        )

    def on_view_all_stories(self, event):
        """
        Open GUI for viewing all stories.

        Args:
            event: wx.Event
        """
        self.Hide()

        # Request server to prepare stories display
        response = self.client_ref._send_request(
            'GET_IMAGES_OF_ALL_VIDEOS',
            {},
        )
        print(f"[DEBUG] Stories display response: {response}")

        # Show stories grid
        show_all_stories(self.client_ref, parent_menu=self)

    def on_post_story(self, event):
        """
        Open camera window to post a new story.

        Args:
            event: wx.Event
        """
        # Create callbacks
        on_post_callback = self._create_post_callback()
        on_closed_callback = self._create_closed_callback()

        # Open camera frame
        StoryCameraFrame(
            parent=None,
            username=self.username,
            on_post_callback=on_post_callback,
            closed_callback=on_closed_callback
        )

    def on_back(self, event):
        """
        Return to main menu.

        Args:
            event: wx.Event
        """
        self.Close()

        # Show parent menu if it exists
        if self.parent_menu:
            self.parent_menu.Show()

    def _create_post_callback(self):
        """
        Create callback for story posting.

        Returns:
            callable: Callback function
        """

        def on_post_callback(caption, media_type, media_data):
            """
            Handle story post completion.

            Args:
                caption: Story caption
                media_type: Type of media (photo/video)
                media_data: Base64 encoded media data
            """
            self.client_ref.on_story_post_callback(
                caption,
                media_type,
                media_data,
            )
        return on_post_callback

    def _create_closed_callback(self):
        """
        Create callback for camera window close.

        Returns:
            callable: Callback function
        """

        def on_closed_callback():
            """Handle camera window closure."""
            print("[INFO] Camera window closed")

        return on_closed_callback
