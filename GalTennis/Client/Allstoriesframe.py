"""
Gal Haham
Main frame for displaying all stories in a grid.
Manages the story grid display window and menu navigation.
REFACTORED: Separated class, all constants added.
"""
import wx
from Storygridpanel import StoryGridPanel

# Window Configuration
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_TITLE = "All Stories"


class AllStoriesFrame(wx.Frame):
    """
    Main frame for displaying all stories in a grid.

    Features:
    - Contains StoryGridPanel for story display
    - Handles window close events
    - Returns to parent menu when closed

    REFACTORED: All constants added, comprehensive documentation.
    """

    def __init__(self, client_ref, parent_menu=None):
        """
        Initialize the all stories display frame.

        Args:
            client_ref: Client instance for server communication
            parent_menu: Reference to StoriesMenuFrame (optional)
        """
        super().__init__(
            None,
            title=WINDOW_TITLE,
            size=(WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        self.client_ref = client_ref
        self.parent_menu = parent_menu

        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close_window)

        # Create main panel
        panel = StoryGridPanel(self, client_ref)

        self.Centre()
        self.Show()

    def on_close_window(self, event):
        """
        Handle window close - return to stories menu.

        Args:
            event: wx.CloseEvent
        """
        # Show parent menu if it exists
        if self.parent_menu:
            self.parent_menu.Show()

        # Continue with close
        event.Skip()
