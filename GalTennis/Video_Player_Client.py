"""
Gal Haham
Video & audio streaming client with GUI
"""
import socket      # Used to create network connections (TCP/IP)
import cv2         # Used for displaying video frames
import pickle      # Used for serializing and deserializing Python objects
import struct      # Used for packing/unpacking binary data (message size)
import wx          # Used for creating the GUI (window, buttons, labels)
import threading   # Used to handle background tasks without freezing the GUI
import pyaudio     # Used for playing audio in real time

DEFAULT_CLIENT_HOST = '127.0.0.1'      # Default server IP (localhost)
DEFAULT_CLIENT_PORT = 9999             # Default port to connect to
NETWORK_HEADER_LENGTH_BYTES = 4        # Number of bytes used for message
FIRST_TUPLE_INDEX = 0                  # Used when unpacking tuples
WINDOW_POSITION_X = 100                # Window X position on the screen
WINDOW_POSITION_Y = 50                 # Window Y position on the screen
INITIAL_FRAME_COUNT = 0                # Start counting frames from 0
FRAME_INCREMENT_STEP = 1               # Increase frame count by 1 each time
KEYBOARD_WAIT_TIME_MS = 1    # Time to wait for key input in milliseconds
KEY_CODE_MASK_8BIT = 0xFF              # Mask to keep last 8 bits of a key code
ESCAPE_KEY_CODE = 27                   # Key code for ESC
WINDOW_NOT_VISIBLE_THRESHOLD = 1       # Window closed threshold (< 1 = closed)
WINDOW_WIDTH = 500                     # Width of GUI window
WINDOW_HEIGHT = 320                    # Height of GUI window
BACKGROUND_COLOR_RED = 240             # Red color for background
BACKGROUND_COLOR_GREEN = 240           # Green color for background
BACKGROUND_COLOR_BLUE = 240            # Blue color for background
TITLE_FONT_SIZE = 14                   # Font size for title text
TITLE_POSITION_X = 20                  # X position for title label
TITLE_POSITION_Y = 15                  # Y position for title label
LABEL_SERVER_IP_POS_X = 20             # X position of "Server IP" label
LABEL_SERVER_IP_POS_Y = 60             # Y position of "Server IP" label
HOST_INPUT_DEFAULT_VALUE = "127.0.0.1"   # Default server IP in input field
HOST_INPUT_POS_X = 120                 # X position for host input box
HOST_INPUT_POS_Y = 57                  # Y position for host input box
HOST_INPUT_WIDTH = 200                 # Width of host input box
HOST_INPUT_HEIGHT = 25                 # Height of host input box
LABEL_PORT_POS_X = 20                  # X position for "Port" label
LABEL_PORT_POS_Y = 95                  # Y position for "Port" label
PORT_INPUT_DEFAULT_VALUE = "9999"      # Default port value
PORT_INPUT_POS_X = 120                 # X position for port input box
PORT_INPUT_POS_Y = 92                  # Y position for port input box
PORT_INPUT_WIDTH = 100                 # Width of port input box
PORT_INPUT_HEIGHT = 25                 # Height of port input box
STATUS_LABEL_POS_X = 20                # X position for status label
STATUS_LABEL_POS_Y = 130               # Y position for status label
STATUS_TEXT_COLOR_RED = 150            # Default red value for status text
STATUS_TEXT_COLOR_GREEN = 150          # Default green value for status text
STATUS_TEXT_COLOR_BLUE = 150           # Default blue value for status text
INFO_LABEL_POS_X = 20                  # X position for info text
INFO_LABEL_POS_Y = 155                 # Y position for info text
INFO_TEXT_COLOR_RED = 150              # Red color for info text
INFO_TEXT_COLOR_GREEN = 100            # Green color for info text
INFO_TEXT_COLOR_BLUE = 50              # Blue color for info text
INFO_FONT_SIZE = 8                     # Small font size for info text
CONNECT_BUTTON_POS_X = 150             # X position for connect button
CONNECT_BUTTON_POS_Y = 190             # Y position for connect button
CONNECT_BUTTON_WIDTH = 200             # Width of connect button
CONNECT_BUTTON_HEIGHT = 40             # Height of connect button
CONNECT_BUTTON_COLOR_RED = 76          # Red color for connect button
CONNECT_BUTTON_COLOR_GREEN = 175       # Green color for connect button
CONNECT_BUTTON_COLOR_BLUE = 80         # Blue color for connect button
INSTRUCTIONS_POS_X = 20                # X position for instructions label
INSTRUCTIONS_POS_Y = 260               # Y position for instructions label
INSTRUCTIONS_TEXT_COLOR_RED = 100      # Red color for instructions text
INSTRUCTIONS_TEXT_COLOR_GREEN = 100    # Green color for instructions text
INSTRUCTIONS_TEXT_COLOR_BLUE = 100     # Blue color for instructions text
STATUS_ACTIVE_COLOR_RED = 255          # Red color when connecting
STATUS_ACTIVE_COLOR_GREEN = 165        # Orange tone when connecting
STATUS_ACTIVE_COLOR_BLUE = 0           # Blue tone when connecting
STATUS_CONNECTED_COLOR_RED = 0         # Red color when connected
STATUS_CONNECTED_COLOR_GREEN = 150     # Green color when connected
STATUS_CONNECTED_COLOR_BLUE = 0        # Blue color when connected
ERROR_COLOR_RED = 200           # Red color for connection error
ERROR_COLOR_GREEN = 0           # Green color for connection error
ERROR_COLOR_BLUE = 0            # Blue color for connection error


class VideoAudioClient:
    def __init__(self, host=DEFAULT_CLIENT_HOST, port=DEFAULT_CLIENT_PORT):
        self.host = host  # Server IP
        self.port = port  # Server port
        self.socket = None  # Network socket for communication
        self.stream_info = None  # Stream information
        self.is_playing = False  # Indicates if video/audio
        self.stop_flag = threading.Event()  # Event flag to stop streaming
        self.audio_stream = None  # PyAudio stream for playing sound
        self.pyaudio_instance = None  # PyAudio instance to manage audio

    def _connect_to_server(self):
        """Creates the TCP socket and attempts to connect to the server."""
        # Create TCP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))  # Connect to server
        print(f"Connected to server {self.host}:{self.port}")
        return True

    def _receive_stream_info(self):
        """Receives the initial handshake packet containing stream metadata."""
        # Receive 4 bytes for message size
        info_size_data = self.recv_all(NETWORK_HEADER_LENGTH_BYTES)
        if not info_size_data:  # No response → fail
            raise ConnectionError("Failed to receive stream info size.")

        # Decode the message size
        info_size = struct.unpack("!L", info_size_data)[FIRST_TUPLE_INDEX]
        info_data = self.recv_all(info_size)  # Receive stream info bytes
        if not info_data:
            raise ConnectionError("Failed to receive stream info data.")

        # Deserialize stream info dict
        self.stream_info = pickle.loads(info_data)

        # Print received stream details
        print(f"Stream Info: ")
        print(
            f"   Video: {self.stream_info['width']}x"
            f"{self.stream_info['height']}"
        )
        print(f"   FPS: {self.stream_info['fps']:.2f}")
        print(f"   Frames: {self.stream_info['total_frames']}")
        print(
            f"   Audio: {self.stream_info['audio_sample_rate']} Hz, "
            f"{self.stream_info['audio_channels']} ch"
        )
        print(f"   Has Audio: {self.stream_info['has_audio']}")
        return True

    def _initialize_audio(self):
        """Initializes PyAudio playback if the stream includes audio."""
        if self.stream_info and self.stream_info['has_audio']:
            try:
                self.pyaudio_instance = pyaudio.PyAudio()
                # Open playback stream
                self.audio_stream = self.pyaudio_instance.open(
                    # Audio format (16-bit PCM)
                    format=pyaudio.paInt16,
                    # Number of channels
                    channels=self.stream_info['audio_channels'],
                    # Sampling rate
                    rate=self.stream_info['audio_sample_rate'],
                    # Enable output
                    output=True,
                    # Buffer size
                    frames_per_buffer=self.stream_info['samples_per_frame']
                )
                print("Audio initialized")
            except Exception as e:
                print(f"Audio initialization failed: {e}")
                # Disable audio on failure
                self.stream_info['has_audio'] = False
        return True

    def connect(self):
        """Orchestrates the connection process: connect,
        receive info, init audio."""
        try:
            # 1. Connect to server
            self._connect_to_server()

            # 2. Receive Stream Info
            self._receive_stream_info()

            # 3. Initialize Audio
            self._initialize_audio()

            return True  # Connection and setup successful

        except Exception as e:
            print(f"Connection error: {e}")  # Print connection error
            if self.socket:
                self.socket.close()
            return False  # Return failure

    def recv_all(self, size):
        """Receive an exact number of bytes from the socket"""
        data = b''  # Empty bytes buffer
        # Loop until all bytes received
        while len(data) < size:
            # Receive remaining bytes
            packet = self.socket.recv(size - len(data))
            if not packet:  # If no data, connection lost
                return None
            data += packet  # Add new data to buffer
        return data  # Return complete data

    def receive_packet(self):
        """Receive one full packet (video frame + audio chunk)"""
        try:
            # Read packet header (size)
            packet_size_data = self.recv_all(NETWORK_HEADER_LENGTH_BYTES)
            if not packet_size_data:
                return None
            # Decode size value
            packet_size = (
                struct.unpack("!L", packet_size_data)
                [FIRST_TUPLE_INDEX]
            )
            packet_data = self.recv_all(packet_size)  # Read entire packet

            if not packet_data:
                return None

            packet = pickle.loads(packet_data)  # Deserialize packet
            return packet  # Return frame+audio data

        except Exception as e:
            print(f"Error receiving packet: {e}")  # Handle receive errors
            return None

    def play_stream(self):
        """Manages the video and audio stream playback loop."""
        if not self.stream_info:
            print("No stream info available")
            return

        window_name = "Video & Audio Stream"
        self._setup_window(window_name)

        self.is_playing = True
        frame_count = INITIAL_FRAME_COUNT
        print("Playing video & audio stream...")

        while not self.stop_flag.is_set():
            packet = self.receive_packet()
            if packet is None:
                print("Stream ended")
                break

            frame_count = self._process_packet(
                window_name,
                packet,
                frame_count
            )

            if self._check_user_input(window_name):
                break

        self.is_playing = False
        self._teardown_window()
        self.cleanup()
        print(f"Received {frame_count} frames")

    def _setup_window(self, window_name):
        """Initializes and configures the OpenCV
         display window based on stream info."""
        # Create adjustable window
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        # Resize window to video size
        cv2.resizeWindow(window_name,
                         self.stream_info['width'],
                         self.stream_info['height'])
        # Move window on screen
        cv2.moveWindow(window_name, WINDOW_POSITION_X, WINDOW_POSITION_Y)

    def _process_packet(self, window_name, packet, frame_count):
        """Displays the video frame and plays the audio chunk from a packet."""
        frame = packet['frame']
        cv2.imshow(window_name, frame)  # Display frame on screen
        frame_count += FRAME_INCREMENT_STEP

        # If audio exists, try to play it
        if self.audio_stream and packet['audio'] is not None:
            self._play_audio_chunk(packet['audio'])

        return frame_count

    def _play_audio_chunk(self, audio_chunk):
        """Converts the audio chunk to bytes and
        writes it to the audio stream."""
        try:
            audio_bytes = audio_chunk.tobytes()
            self.audio_stream.write(audio_bytes)
        except Exception as e:
            # Handle playback error
            print(f"Audio playback error: {e}")

    @staticmethod
    def _check_user_input(window_name):
        """Checks for user input (Q/ESC) or manual window closing."""
        # Check keyboard press
        key = cv2.waitKey(KEYBOARD_WAIT_TIME_MS) & KEY_CODE_MASK_8BIT

        # Q or ESC pressed → stop
        if key == ord('q') or key == ESCAPE_KEY_CODE:
            print("Stopped by user")
            return True

        # Check if window manually closed
        if (cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) <
                WINDOW_NOT_VISIBLE_THRESHOLD):
            print("Window closed")
            return True

        return False  # Continue loop

    @staticmethod
    def _teardown_window():
        """Cleans up OpenCV resources."""
        cv2.destroyAllWindows()

    def cleanup(self):
        """Release resources and close connections"""
        if self.audio_stream:  # Stop audio if running
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.pyaudio_instance:  # Terminate PyAudio
            self.pyaudio_instance.terminate()
        if self.socket:  # Close socket connection
            self.socket.close()
            print("Disconnected from server")  # Log disconnection


class VideoAudioClientFrame(wx.Frame):
    """Graphical User Interface for Video & Audio Client"""

    def __init__(self):
        super().__init__(
            None,
            title="Video & Audio Stream Client",
            size=wx.Size(WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        panel = wx.Panel(self)   # Create panel inside window
        panel.SetBackgroundColour(
            wx.Colour(
                BACKGROUND_COLOR_RED,
                BACKGROUND_COLOR_GREEN,
                BACKGROUND_COLOR_BLUE
            )
        )

        # ----- Title -----
        title_font = wx.Font(
            TITLE_FONT_SIZE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title = wx.StaticText(panel, label="Video & Audio Stream Client",
                              pos=wx.Point(TITLE_POSITION_X, TITLE_POSITION_Y))
        title.SetFont(title_font)  # Set font for title

        # ----- Server Settings -----
        wx.StaticText(
            panel,
            label="Server IP:",
            pos=wx.Point(LABEL_SERVER_IP_POS_X, LABEL_SERVER_IP_POS_Y)
        )
        self.host_input = wx.TextCtrl(
            panel,
            value=HOST_INPUT_DEFAULT_VALUE,
            pos=wx.Point(HOST_INPUT_POS_X, HOST_INPUT_POS_Y),
            size=wx.Size(HOST_INPUT_WIDTH, HOST_INPUT_HEIGHT)
        )

        wx.StaticText(
            panel,
            label="Port:",
            pos=wx.Point(LABEL_PORT_POS_X, LABEL_PORT_POS_Y)
        )
        self.port_input = wx.TextCtrl(
            panel,
            value=PORT_INPUT_DEFAULT_VALUE,
            pos=wx.Point(PORT_INPUT_POS_X, PORT_INPUT_POS_Y),
            size=wx.Size(PORT_INPUT_WIDTH, PORT_INPUT_HEIGHT)
        )

        # ----- Status Label -----
        self.status_text = wx.StaticText(
            panel,
            label="Status: Not connected",
            pos=wx.Point(STATUS_LABEL_POS_X, STATUS_LABEL_POS_Y)
        )
        self.status_text.SetForegroundColour(wx.Colour(
            STATUS_TEXT_COLOR_RED,
            STATUS_TEXT_COLOR_GREEN,
            STATUS_TEXT_COLOR_BLUE
        ))

        # ----- Info Text -----
        info = wx.StaticText(
            panel,
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

        # ----- Connect Button -----
        self.connect_btn = wx.Button(
            panel,
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

        # ----- Instructions -----
        instructions = wx.StaticText(
            panel,
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

        # ----- Event Bindings -----
        # When button clicked → on_connect
        self.connect_btn.Bind(wx.EVT_BUTTON, self.on_connect)
        self.Bind(wx.EVT_CLOSE, self.on_close)  # When window closes → on_close

        self.client = None  # Placeholder for client instance
        self.Centre()   # Center window on screen
        self.Show()  # Display window

    def on_connect(self, _event):
        """Handle 'Connect & Play' button click"""
        host = self.host_input.GetValue()  # Get IP from input field
        port = int(self.port_input.GetValue())  # Convert port input to integer
        # Update label to "connecting"
        self.status_text.SetLabel("Status: Connecting...")
        self.status_text.SetForegroundColour(
            wx.Colour(
                STATUS_ACTIVE_COLOR_RED,
                STATUS_ACTIVE_COLOR_GREEN,
                STATUS_ACTIVE_COLOR_BLUE
            )
        )

        self.client = VideoAudioClient(host, port)  # Create client object

        if self.client.connect():   # If connection success
            self.status_text.SetLabel("Status: Connected - Playing...")
            self.status_text.SetForegroundColour(
                wx.Colour(
                    STATUS_CONNECTED_COLOR_RED,
                    STATUS_CONNECTED_COLOR_GREEN,
                    STATUS_CONNECTED_COLOR_BLUE
                )
            )
            play_thread = threading.Thread(target=self.client.play_stream)
            # Start playback in new thread
            play_thread.daemon = True
            play_thread.start()
        else:  # If connection fails
            self.status_text.SetLabel("Status: Connection failed")
            self.status_text.SetForegroundColour(wx.Colour(ERROR_COLOR_RED,
                                                           ERROR_COLOR_GREEN,
                                                           ERROR_COLOR_BLUE))

    def on_close(self, _event):
        """Handle window close event"""
        if self.client:
            self.client.stop_flag.set()  # Stop video playback loop
            self.client.cleanup()  # Clean resources
        cv2.destroyAllWindows()  # Ensure video window closes
        self.Destroy()  # Close GUI window


def run_video_player_client():
    app = wx.App()  # Initialize wxPython application
    VideoAudioClientFrame()   # Create and show the main window
    app.MainLoop()   # Run the GUI event loop
