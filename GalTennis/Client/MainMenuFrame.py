"""
Gal Haham
Main menu frame - primary navigation hub after login.
Provides access to videos and stories features with styled exit dialog.
REFACTORED: All magic numbers replaced with constants,
comprehensive documentation.
"""
import wx
from VideoMenuFrame import VideoMenuFrame
from StoriesMenuFrame import StoriesMenuFrame


# Window Configuration
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 300
WINDOW_TITLE = "Main Menu"

# Dialog Configuration
DIALOG_WIDTH = 450
DIALOG_HEIGHT = 300
DIALOG_TITLE = "Tennis Social"

# Colors
COLOR_BACKGROUND = wx.Colour(245, 245, 245)
COLOR_HEADER = wx.Colour(40, 120, 80)
COLOR_GOODBYE = wx.Colour(40, 120, 80)
COLOR_THANKS = wx.Colour(100, 100, 100)
COLOR_USER_MESSAGE = wx.Colour(150, 150, 150)
COLOR_WHITE = wx.WHITE

# Fonts
FONT_SIZE_WELCOME = 16
FONT_SIZE_ICON = 48
FONT_SIZE_DIALOG_TITLE = 20
FONT_SIZE_GOODBYE = 18
FONT_SIZE_THANKS = 12
FONT_SIZE_USER_MESSAGE = 10

# Button Sizes
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 40

# Spacing
SPACING_WELCOME_TOP = 20
SPACING_BUTTON_VIDEOS = 20
SPACING_BUTTON_STORIES = 15
SPACING_BUTTON_QUIT = 25
SPACING_ICON_TOP = 20
SPACING_TITLE_TOP = 10
SPACING_GOODBYE_TOP = 25
SPACING_THANKS_TOP = 10
SPACING_USER_TOP = 15

# Timing
DIALOG_DISPLAY_TIME_MS = 2000
EXIT_DELAY_MS = 500
EXIT_CODE_SUCCESS = 0


class MainMenuFrame(wx.Frame):
    """
    Main GUI menu after login.

    Features:
    - Navigate to Videos menu
    - Navigate to Stories menu
    - Quit application with styled dialog

    REFACTORED: All magic numbers replaced with constants.
    """

    def __init__(self, username, client_ref):
        """
        Initialize the main menu frame.

        Args:
            username: Current user's username
            client_ref: Client instance for server communication
        """
        super().__init__(
            parent=None,
            title=WINDOW_TITLE,
            size=(WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        self.username = username
        self.client_ref = client_ref

        self._init_ui()

        self.Centre()
        self.Show()

    def _init_ui(self):
        """Initialize the user interface."""
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Welcome message
        self._add_welcome_message(panel, vbox)

        # Menu buttons
        self._add_menu_buttons(panel, vbox)

        panel.SetSizer(vbox)

    def _add_welcome_message(self, panel, vbox):
        """
        Add welcome message with username.

        Args:
            panel: Parent panel
            vbox: Vertical sizer
        """
        title = wx.StaticText(panel, label=f"Welcome, {self.username}!")
        title_font = wx.Font(
            FONT_SIZE_WELCOME,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title.SetFont(title_font)
        vbox.Add(
            title,
            flag=wx.ALIGN_CENTER | wx.TOP,
            border=SPACING_WELCOME_TOP,
        )

    def _add_menu_buttons(self, panel, vbox):
        """
        Add menu navigation buttons.

        Args:
            panel: Parent panel
            vbox: Vertical sizer
        """
        # Videos button
        videos_btn = wx.Button(
            panel,
            label="Videos (View / Upload)",
            size=(BUTTON_WIDTH, BUTTON_HEIGHT)
        )
        videos_btn.Bind(wx.EVT_BUTTON, self.on_videos)
        vbox.Add(
            videos_btn,
            flag=wx.ALIGN_CENTER | wx.TOP,
            border=SPACING_BUTTON_VIDEOS,
        )
        # Stories button
        stories_btn = wx.Button(
            panel,
            label="Stories (View / Post)",
            size=(BUTTON_WIDTH, BUTTON_HEIGHT)
        )
        stories_btn.Bind(wx.EVT_BUTTON, self.on_stories)
        vbox.Add(
            stories_btn,
            flag=wx.ALIGN_CENTER | wx.TOP,
            border=SPACING_BUTTON_STORIES,
        )
        # Quit button
        quit_btn = wx.Button(
            panel,
            label="Quit",
            size=(BUTTON_WIDTH, BUTTON_HEIGHT),
        )
        quit_btn.Bind(wx.EVT_BUTTON, self.on_quit)
        vbox.Add(
            quit_btn,
            flag=wx.ALIGN_CENTER | wx.TOP,
            border=SPACING_BUTTON_QUIT,
        )

    def on_videos(self, event):
        """
        Open Videos menu and hide main menu.

        Args:
            event: wx.Event
        """
        self.Hide()
        VideoMenuFrame(client=self.client_ref, parent_menu=self)

    def on_stories(self, event):
        """
        Open Stories menu and hide main menu.

        Args:
            event: wx.Event
        """
        self.Hide()
        StoriesMenuFrame(
            username=self.username,
            client_ref=self.client_ref,
            parent_menu=self
        )

    def on_quit(self, event):
        """
        Quit application with goodbye dialog.

        Args:
            event: wx.Event
        """
        self.close_application()

    def close_application(self):
        """Properly close the entire application with goodbye dialog."""
        # Show styled goodbye dialog
        dialog = self._create_goodbye_dialog()
        dialog.Show()

        # Schedule cleanup after dialog is visible
        wx.CallLater(
            DIALOG_DISPLAY_TIME_MS,
            lambda: self._finish_closing(dialog),
        )

    def _finish_closing(self, dialog):
        """
        Complete the closing process after dialog display.

        Args:
            dialog: Goodbye dialog to close
        """
        dialog.Close()

        # Close all windows except self and dialog
        for window in wx.GetTopLevelWindows():
            if window != self and window != dialog:
                window.Close(True)

        # Destroy main frame
        self.Destroy()

        # Exit main loop
        app = wx.App.Get()
        if app:
            app.ExitMainLoop()

        # Force exit after cleanup
        wx.CallLater(EXIT_DELAY_MS, self._force_exit)

    def _create_goodbye_dialog(self):
        """
        Create styled goodbye message dialog.

        Returns:
            wx.Dialog: Configured goodbye dialog
        """
        dialog = wx.Dialog(
            self,
            title=DIALOG_TITLE,
            size=(DIALOG_WIDTH, DIALOG_HEIGHT),
            style=wx.CAPTION | wx.STAY_ON_TOP
        )
        dialog.SetBackgroundColour(COLOR_BACKGROUND)

        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Top panel (green header)
        top_panel = self._create_dialog_header(dialog)
        main_sizer.Add(top_panel, 1, wx.EXPAND)

        # Bottom panel (goodbye message)
        bottom_panel = self._create_dialog_message(dialog)
        main_sizer.Add(bottom_panel, 1, wx.EXPAND)

        dialog.SetSizer(main_sizer)
        dialog.Centre()

        return dialog

    def _create_dialog_header(self, parent):
        """
        Create dialog header with icon and title.

        Args:
            parent: Parent dialog

        Returns:
            wx.Panel: Header panel
        """
        top_panel = wx.Panel(parent)
        top_panel.SetBackgroundColour(COLOR_HEADER)
        top_sizer = wx.BoxSizer(wx.VERTICAL)

        # Tennis icon
        icon_text = wx.StaticText(top_panel, label="")
        icon_font = wx.Font(
            FONT_SIZE_ICON,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        icon_text.SetFont(icon_font)
        top_sizer.Add(icon_text, 0, wx.ALIGN_CENTER | wx.TOP, SPACING_ICON_TOP)

        # Title
        title = wx.StaticText(top_panel, label="Tennis Social")
        title.SetForegroundColour(COLOR_WHITE)
        title_font = wx.Font(
            FONT_SIZE_DIALOG_TITLE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title.SetFont(title_font)
        top_sizer.Add(title, 0, wx.ALIGN_CENTER | wx.TOP, SPACING_TITLE_TOP)

        top_panel.SetSizer(top_sizer)
        return top_panel

    def _create_dialog_message(self, parent):
        """
        Create dialog message section.

        Args:
            parent: Parent dialog

        Returns:
            wx.Panel: Message panel
        """
        bottom_panel = wx.Panel(parent)
        bottom_panel.SetBackgroundColour(COLOR_BACKGROUND)
        bottom_sizer = wx.BoxSizer(wx.VERTICAL)

        # Goodbye message
        goodbye_text = wx.StaticText(bottom_panel, label="Goodbye!")
        goodbye_text.SetForegroundColour(COLOR_GOODBYE)
        goodbye_font = wx.Font(
            FONT_SIZE_GOODBYE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        goodbye_text.SetFont(goodbye_font)
        bottom_sizer.Add(
            goodbye_text,
            0,
            wx.ALIGN_CENTER | wx.TOP,
            SPACING_GOODBYE_TOP,
        )
        # Thank you message
        thanks_text = wx.StaticText(
            bottom_panel,
            label="Thanks for using Tennis Social!"
        )
        thanks_text.SetForegroundColour(COLOR_THANKS)
        thanks_font = wx.Font(
            FONT_SIZE_THANKS,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        thanks_text.SetFont(thanks_font)
        bottom_sizer.Add(
            thanks_text,
            0,
            wx.ALIGN_CENTER | wx.TOP,
            SPACING_THANKS_TOP,
        )
        # Username specific message
        user_text = wx.StaticText(
            bottom_panel,
            label=f"See you next time, {self.username}! "
        )
        user_text.SetForegroundColour(COLOR_USER_MESSAGE)
        user_font = wx.Font(
            FONT_SIZE_USER_MESSAGE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_ITALIC,
            wx.FONTWEIGHT_NORMAL
        )
        user_text.SetFont(user_font)
        bottom_sizer.Add(
            user_text,
            0,
            wx.ALIGN_CENTER | wx.TOP,
            SPACING_USER_TOP,
        )
        bottom_panel.SetSizer(bottom_sizer)
        return bottom_panel

    def _force_exit(self):
        """Force exit to close all threads."""
        import sys
        sys.exit(EXIT_CODE_SUCCESS)
