import wx                      # Imports the wxPython library for GUI development.
import socket                  # Imports the standard socket library
import json                    # Imports the json module for data serialization/deserialization.
from Protocol import Protocol  # Imports the custom Protocol module

# --- Configuration ---
HOST = '127.0.0.1'             # Defines the server's IP address.
PORT = 5000                    # Defines the server's port number.


class LoginFrame(wx.Frame):    # Defines the main window class, inheriting from wx.Frame.
    def __init__(self):        # Constructor method.
        super().__init__(parent=None, title='Tennis Social - Login', size=wx.Size(400, 550))

        # Store login result
        self.logged_in_username = None
        self.login_success = False

        self.username_input = None
        self.password_input = None
        self.login_btn = None

        # Set black background
        self.SetBackgroundColour(wx.Colour(0, 0, 0))

        # Center the frame on screen
        self.Centre()

        # Create UI
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        # Create main panel
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(0, 0, 0))

        # Create main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Add spacing at top
        main_sizer.AddSpacer(50)

        # Title
        title = wx.StaticText(panel, label='Welcome Back')
        title.SetForegroundColour(wx.Colour(255, 255, 255))
        font_title = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(font_title)
        main_sizer.Add(title, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        # Subtitle
        subtitle = wx.StaticText(panel, label='Please login to continue')
        subtitle.SetForegroundColour(wx.Colour(153, 153, 153))
        font_subtitle = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        subtitle.SetFont(font_subtitle)
        main_sizer.Add(subtitle, 0, wx.ALIGN_CENTER | wx.BOTTOM, 40)

        # Form container
        form_sizer = wx.BoxSizer(wx.VERTICAL)

        # Username label
        username_label = wx.StaticText(panel, label='Username')
        username_label.SetForegroundColour(wx.Colour(204, 204, 204))
        form_sizer.Add(username_label, 0, wx.LEFT | wx.BOTTOM, 8)

        # Username input
        self.username_input = wx.TextCtrl(panel, size=wx.Size(300, 35))
        self.username_input.SetBackgroundColour(wx.Colour(26, 26, 26))
        self.username_input.SetForegroundColour(wx.Colour(255, 255, 255))
        form_sizer.Add(self.username_input, 0, wx.EXPAND | wx.BOTTOM, 20)

        # Password label
        password_label = wx.StaticText(panel, label='Password')
        password_label.SetForegroundColour(wx.Colour(204, 204, 204))
        form_sizer.Add(password_label, 0, wx.LEFT | wx.BOTTOM, 8)

        # Password input
        self.password_input = wx.TextCtrl(panel, size=wx.Size(300, 35), style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        self.password_input.SetBackgroundColour(wx.Colour(26, 26, 26))
        self.password_input.SetForegroundColour(wx.Colour(255, 255, 255))
        form_sizer.Add(self.password_input, 0, wx.EXPAND | wx.BOTTOM, 10)

        # Forgot password link (right-aligned)
        forgot_link = wx.StaticText(panel, label='Forgot password?')
        forgot_link.SetForegroundColour(wx.Colour(136, 136, 136))
        forgot_link.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        forgot_link.Bind(wx.EVT_LEFT_DOWN, self.on_forgot_password)
        form_sizer.Add(forgot_link, 0, wx.ALIGN_RIGHT | wx.BOTTOM, 30)

        # Login button
        self.login_btn = wx.Button(panel, label='Login', size=wx.Size(300, 45))
        self.login_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.login_btn.SetForegroundColour(wx.Colour(0, 0, 0))
        font_btn = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.login_btn.SetFont(font_btn)
        self.login_btn.Bind(wx.EVT_BUTTON, self.on_login)
        form_sizer.Add(self.login_btn, 0, wx.EXPAND | wx.BOTTOM, 20)

        # Sign up section
        signup_sizer = wx.BoxSizer(wx.HORIZONTAL)
        signup_text = wx.StaticText(panel, label="Don't have an account? ")
        signup_text.SetForegroundColour(wx.Colour(153, 153, 153))
        signup_link = wx.StaticText(panel, label='Sign up')
        signup_link.SetForegroundColour(wx.Colour(255, 255, 255))
        signup_link.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        signup_link.Bind(wx.EVT_LEFT_DOWN, self.on_signup_click)

        signup_sizer.Add(signup_text, 0)
        signup_sizer.Add(signup_link, 0)
        form_sizer.Add(signup_sizer, 0, wx.ALIGN_CENTER)

        # Add form to main sizer
        main_sizer.Add(form_sizer, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 50)

        panel.SetSizer(main_sizer)

        # Bind Enter key to login
        self.password_input.Bind(wx.EVT_TEXT_ENTER, self.on_login)

    @staticmethod
    def send_request(request_type, payload):  # Method to handle client-server communication.
        """Send request to server using Protocol"""
        try:
            # Create socket connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Creates a TCP socket object.
            client_socket.connect((HOST, PORT))  # Connects the socket to the defined server HOST and PORT.

            # Prepare request
            request_data = json.dumps({  # Serializes the request dictionary (type and payload) into a JSON string.
                "type": request_type,
                "payload": payload
            })

            # Send using Protocol
            Protocol.send(client_socket, request_data)

            # Receive response using Protocol
            response_data = Protocol.recv(client_socket)
            response = json.loads(response_data)

            client_socket.close()                  # Closes the client socket connection.
            return response                        # Returns the server's response dictionary.

        except ConnectionRefusedError:         # Catches the error if the server is not running or reachable.
            return {"status": "error", "message": "Could not connect to server. Is it running?"}
        except Exception as e:                 # Catches any other network or general exception.
            return {"status": "error", "message": f"Network error: {e}"}  # Returns a general network error message.

    def on_login(self):             # Event handler for the Login button or Enter key press.
        """Handle login button click"""
        username = self.username_input.GetValue().strip()
        password = self.password_input.GetValue().strip()

        # Validation
        if not username or not password:   # Checks if either field is empty.
            wx.MessageBox('Please enter both username and password',  # Displays an error dialog box.
                          'Error', wx.OK | wx.ICON_ERROR)
            return                         # Exits the function.

        # Show loading cursor
        wx.BeginBusyCursor()               # Changes the cursor to an hourglass/busy state.

        # Send login request
        # Creates the payload dictionary for the server.
        payload = {'username': username, 'password': password}
        # Sends the LOGIN request to the server and waits for the response.
        response = self.send_request('LOGIN', payload)

        # Restore cursor
        wx.EndBusyCursor()                 # Restores the cursor to the normal state.

        # Handle response
        if response.get('status') == 'success':  # Checks if the server response indicates success.
            self.logged_in_username = username  # Stores the successfully logged-in username.
            self.login_success = True           # Sets the success flag to True.
            wx.MessageBox(f'Welcome {username}!',  # Displays a success dialog box.
                          'Login Successful', wx.OK | wx.ICON_INFORMATION)
            # Close the window
            self.Close()                    # Closes the login window.
        else:
            error_msg = response.get('message', 'Unknown error')  # Extracts the error message from the response.
            wx.MessageBox(f'Login failed: {error_msg}',  # Displays an error dialog box with the reason.
                          'Login Failed', wx.OK | wx.ICON_ERROR)
            # Clear password field
            self.password_input.Clear()     # Clears the password input field.
            self.password_input.SetFocus()  # Sets the focus back to the password field.

    @staticmethod
    def on_forgot_password():   # Event handler for the 'Forgot password?' link.
        """Handle forgot password click"""
        wx.MessageBox('Please contact the administrator to reset your password.',  # Displays an informational message.
                      'Forgot Password', wx.OK | wx.ICON_INFORMATION)

    def on_signup_click(self):      # Event handler for the 'Sign up' link.
        """Handle sign up link click - Open Signup window"""
        self.Hide()                        # Hides the current login window.
        # Import Signup_UI here to avoid circular imports
        try:
            # Attempts to import the SignupFrame class dynamically.
            from Signup_UI import SignupFrame
            # Creates an instance of the signup frame, passing the login frame as parent.
            signup_frame = SignupFrame(self)
            signup_frame.Show()              # Displays the signup window.
        except ImportError:                  # Catches the error if the Signup_UI file/module is missing.
            wx.MessageBox('Signup window not available yet.',  # Displays an error message.
                          'Error', wx.OK | wx.ICON_ERROR)
            self.Show()                     # Shows the login window again if signup fails to load.


# For testing the UI independently
if __name__ == '__main__':                 # Checks if the script is being run directly (not imported).
    app = wx.App()                         # Creates a wxPython application object.
    frame = LoginFrame()                   # Creates an instance of the LoginFrame.
    frame.Show()                           # Displays the login window.
    app.MainLoop()                         # Starts the main wxPython event loop (keeps the UI running).

    # After window closes, check result
    if frame.login_success:                # Checks the login success flag after the app closes.
        print(f"Login successful! Username: {frame.logged_in_username}")  # Prints success message to console.
    else:
        print("Login cancelled or failed")  # Prints failure message to console.
