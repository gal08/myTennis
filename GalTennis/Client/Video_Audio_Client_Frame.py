"""
Gal Haham
GUI Frame for Video & Audio Client
Provides user interface for connecting to streaming server
REFACTORED: Constructor split into smaller helper methods
"""
import wx
import cv2
import threading
from Read_server_ip import readServerIp
from Video_Audio_Client import VideoAudioClient

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 320
BACKGROUND_COLOR_RED = 240
BACKGROUND_COLOR_GREEN = 240
BACKGROUND_COLOR_BLUE = 240
TITLE_FONT_SIZE = 14
TITLE_POSITION_X = 20
TITLE_POSITION_Y = 15
LABEL_SERVER_IP_POS_X = 20
LABEL_SERVER_IP_POS_Y = 60
HOST_INPUT_DEFAULT_VALUE = readServerIp()
HOST_INPUT_POS_X = 120
HOST_INPUT_POS_Y = 57
HOST_INPUT_WIDTH = 200
HOST_INPUT_HEIGHT = 25
LABEL_PORT_POS_X = 20
LABEL_PORT_POS_Y = 95
PORT_INPUT_DEFAULT_VALUE = "9999"
PORT_INPUT_POS_X = 120
PORT_INPUT_POS_Y = 92
PORT_INPUT_WIDTH = 100
PORT_INPUT_HEIGHT = 25
STATUS_LABEL_POS_X = 20
STATUS_LABEL_POS_Y = 130
STATUS_TEXT_COLOR_RED = 150
STATUS_TEXT_COLOR_GREEN = 150
STATUS_TEXT_COLOR_BLUE = 150
INFO_LABEL_POS_X = 20
INFO_LABEL_POS_Y = 155
INFO_TEXT_COLOR_RED = 150
INFO_TEXT_COLOR_GREEN = 100
INFO_TEXT_COLOR_BLUE = 50
INFO_FONT_SIZE = 8
CONNECT_BUTTON_POS_X = 150
CONNECT_BUTTON_POS_Y = 190
CONNECT_BUTTON_WIDTH = 200
CONNECT_BUTTON_HEIGHT = 40
CONNECT_BUTTON_COLOR_RED = 76
CONNECT_BUTTON_COLOR_GREEN = 175
CONNECT_BUTTON_COLOR_BLUE = 80
INSTRUCTIONS_POS_X = 20
INSTRUCTIONS_POS_Y = 260
INSTRUCTIONS_TEXT_COLOR_RED = 100
INSTRUCTIONS_TEXT_COLOR_GREEN = 100
INSTRUCTIONS_TEXT_COLOR_BLUE = 100
STATUS_ACTIVE_COLOR_RED = 255
STATUS_ACTIVE_COLOR_GREEN = 165
STATUS_ACTIVE_COLOR_BLUE = 0
STATUS_CONNECTED_COLOR_RED = 0
STATUS_CONNECTED_COLOR_GREEN = 150
STATUS_CONNECTED_COLOR_BLUE = 0
ERROR_COLOR_RED = 200
ERROR_COLOR_GREEN = 0
ERROR_COLOR_BLUE = 0


class VideoAudioClientFrame(wx.Frame):
    """Graphical User Interface for Video & Audio Client"""

    def __init__(self):
        """Initialize the frame with split UI creation methods"""
        super().__init__(
            None,
            title="Video & Audio Stream Client",
            size=wx.Size(WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        # Create main panel
        self.panel = self._create_main_panel()

        # Initialize client variable
        self.client = None

        # Build UI components
        self._create_title()
        self._create_server_settings()
        self._create_status_label()
        self._create_info_text()
        self._create_connect_button()
        self._create_instructions()
        self._setup_event_bindings()

        # Show frame
        self.Centre()
        self.Show()

    def _create_main_panel(self):
        """Create and configure the main panel with background color"""
        panel = wx.Panel(self)
        panel.SetBackgroundColour(
            wx.Colour(
                BACKGROUND_COLOR_RED,
                BACKGROUND_COLOR_GREEN,
                BACKGROUND_COLOR_BLUE
            )
        )
        return panel

    def _create_title(self):
        """Create the title text at the top of the window"""
        title_font = wx.Font(
            TITLE_FONT_SIZE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title = wx.StaticText(
            self.panel,
            label="Video & Audio Stream Client",
            pos=wx.Point(TITLE_POSITION_X, TITLE_POSITION_Y)
        )
        title.SetFont(title_font)

    def _create_server_settings(self):
        """Create server IP and port input fields"""
        self._create_ip_input()
        self._create_port_input()

    def _create_ip_input(self):
        """Create the server IP label and input field"""
        wx.StaticText(
            self.panel,
            label="Server IP:",
            pos=wx.Point(LABEL_SERVER_IP_POS_X, LABEL_SERVER_IP_POS_Y)
        )
        self.host_input = wx.TextCtrl(
            self.panel,
            value=HOST_INPUT_DEFAULT_VALUE,
            pos=wx.Point(HOST_INPUT_POS_X, HOST_INPUT_POS_Y),
            size=wx.Size(HOST_INPUT_WIDTH, HOST_INPUT_HEIGHT)
        )

    def _create_port_input(self):
        """Create the port label and input field"""
        wx.StaticText(
            self.panel,
            label="Port:",
            pos=wx.Point(LABEL_PORT_POS_X, LABEL_PORT_POS_Y)
        )
        self.port_input = wx.TextCtrl(
            self.panel,
            value=PORT_INPUT_DEFAULT_VALUE,
            pos=wx.Point(PORT_INPUT_POS_X, PORT_INPUT_POS_Y),
            size=wx.Size(PORT_INPUT_WIDTH, PORT_INPUT_HEIGHT)
        )

    def _create_status_label(self):
        """Create the status label that shows connection state"""
        self.status_text = wx.StaticText(
            self.panel,
            label="Status: Not connected",
            pos=wx.Point(STATUS_LABEL_POS_X, STATUS_LABEL_POS_Y)
        )
        self.status_text.SetForegroundColour(wx.Colour(
            STATUS_TEXT_COLOR_RED,
            STATUS_TEXT_COLOR_GREEN,
            STATUS_TEXT_COLOR_BLUE
        ))

    def _create_info_text(self):
        """Create the information text about requirements"""
        info = wx.StaticText(
            self.panel,
            label="Requires: ffmpeg (server) & pyaudio (client)",
            pos=wx.Point(INFO_LABEL_POS_X, INFO_LABEL_POS_Y)
        )
        info.SetForegroundColour(
            wx.Colour(
                INFO_TEXT_COLOR_RED,
                INFO_TEXT_COLOR_GREEN,
                INFO_TEXT_COLOR_BLUE
            )
        )
        small_font = wx.Font(
            INFO_FONT_SIZE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_ITALIC,
            wx.FONTWEIGHT_NORMAL
        )
        info.SetFont(small_font)

    def _create_connect_button(self):
        """Create the connect button"""
        self.connect_btn = wx.Button(
            self.panel,
            label="Connect & Play",
            pos=wx.Point(CONNECT_BUTTON_POS_X, CONNECT_BUTTON_POS_Y),
            size=wx.Size(CONNECT_BUTTON_WIDTH, CONNECT_BUTTON_HEIGHT)
        )
        self.connect_btn.SetBackgroundColour(
            wx.Colour(
                CONNECT_BUTTON_COLOR_RED,
                CONNECT_BUTTON_COLOR_GREEN,
                CONNECT_BUTTON_COLOR_BLUE
            )
        )
        self.connect_btn.SetForegroundColour(wx.WHITE)

    def _create_instructions(self):
        """Create the instructions text at the bottom"""
        instructions = wx.StaticText(
            self.panel,
            label="Press Q or ESC in video window to stop",
            pos=wx.Point(INSTRUCTIONS_POS_X, INSTRUCTIONS_POS_Y)
        )
        instructions.SetForegroundColour(
            wx.Colour(
                INSTRUCTIONS_TEXT_COLOR_RED,
                INSTRUCTIONS_TEXT_COLOR_GREEN,
                INSTRUCTIONS_TEXT_COLOR_BLUE
            )
        )

    def _setup_event_bindings(self):
        """Set up all event bindings"""
        self.connect_btn.Bind(wx.EVT_BUTTON, self.on_connect)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_connect(self, _event):
        """Handle 'Connect & Play' button click"""
        host = self.host_input.GetValue()
        port = int(self.port_input.GetValue())

        self._update_status_connecting()

        self.client = VideoAudioClient(host, port)

        if self.client.connect():
            self._update_status_connected()
            self._start_playback_thread()
        else:
            self._update_status_failed()

    def _update_status_connecting(self):
        """Update status to show connecting state"""
        self.status_text.SetLabel("Status: Connecting...")
        self.status_text.SetForegroundColour(
            wx.Colour(
                STATUS_ACTIVE_COLOR_RED,
                STATUS_ACTIVE_COLOR_GREEN,
                STATUS_ACTIVE_COLOR_BLUE
            )
        )

    def _update_status_connected(self):
        """Update status to show connected and playing state"""
        self.status_text.SetLabel("Status: Connected - Playing...")
        self.status_text.SetForegroundColour(
            wx.Colour(
                STATUS_CONNECTED_COLOR_RED,
                STATUS_CONNECTED_COLOR_GREEN,
                STATUS_CONNECTED_COLOR_BLUE
            )
        )

    def _update_status_failed(self):
        """Update status to show connection failed"""
        self.status_text.SetLabel("Status: Connection failed")
        self.status_text.SetForegroundColour(
            wx.Colour(
                ERROR_COLOR_RED,
                ERROR_COLOR_GREEN,
                ERROR_COLOR_BLUE
            )
        )

    def _start_playback_thread(self):
        """Start the video playback in a separate thread"""
        play_thread = threading.Thread(target=self.client.play_stream)
        play_thread.daemon = True
        play_thread.start()

    def on_close(self, _event):
        """Handle window close event"""
        if self.client:
            self.client.stop_flag.set()
            self.client.cleanup()
        cv2.destroyAllWindows()
        self.Destroy()
