"""
Gal Haham
Main frame for displaying all videos in a grid.
Manages the video grid display window and menu navigation.
REFACTORED: Separated class, all constants added.
"""
import wx
from Videogridpanel import VideoGridPanel


# Window Configuration
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_TITLE = "🎬 All Videos"


class AllVideosFrame(wx.Frame):
    """
    Main frame for displaying all videos in a grid.

    Features:
    - Contains VideoGridPanel for video display
    - Handles window close events
    - Returns to parent menu when closed

    REFACTORED: All constants added, comprehensive documentation.
    """

    def __init__(self, client_ref, parent_menu=None):
        """
        Initialize the all videos display frame.

        Args:
            client_ref: Client instance for server communication
            parent_menu: Reference to VideoMenuFrame (optional)
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
        panel = VideoGridPanel(self, client_ref)

        self.Centre()
        self.Show()

    def on_close_window(self, event):
        """
        Handle window close - return to videos menu.

        Args:
            event: wx.CloseEvent
        """
        # Show parent menu if it exists
        if self.parent_menu:
            self.parent_menu.Show()

        # Continue with close
        event.Skip()
