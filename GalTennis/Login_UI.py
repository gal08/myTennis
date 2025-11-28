import wx
import socket
import json
from Protocol import Protocol

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 5000


class LoginFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='Tennis Social - Login', size=(400, 550))

        # Store login result
        self.logged_in_username = None
        self.login_success = False

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
        self.username_input = wx.TextCtrl(panel, size=(300, 35))
        self.username_input.SetBackgroundColour(wx.Colour(26, 26, 26))
        self.username_input.SetForegroundColour(wx.Colour(255, 255, 255))
        form_sizer.Add(self.username_input, 0, wx.EXPAND | wx.BOTTOM, 20)

        # Password label
        password_label = wx.StaticText(panel, label='Password')
        password_label.SetForegroundColour(wx.Colour(204, 204, 204))
        form_sizer.Add(password_label, 0, wx.LEFT | wx.BOTTOM, 8)

        # Password input
        self.password_input = wx.TextCtrl(panel, size=(300, 35), style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
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
        self.login_btn = wx.Button(panel, label='Login', size=(300, 45))
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

    def send_request(self, request_type, payload):
        """Send request to server using Protocol"""
        try:
            # Create socket connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((HOST, PORT))

            # Prepare request
            request_data = json.dumps({
                "type": request_type,
                "payload": payload
            })

            # Send using Protocol
            Protocol.send(client_socket, request_data)

            # Receive response using Protocol
            response_data = Protocol.recv(client_socket)
            response = json.loads(response_data)

            client_socket.close()
            return response

        except ConnectionRefusedError:
            return {"status": "error", "message": "Could not connect to server. Is it running?"}
        except Exception as e:
            return {"status": "error", "message": f"Network error: {e}"}

    def on_login(self, event):
        """Handle login button click"""
        username = self.username_input.GetValue().strip()
        password = self.password_input.GetValue().strip()

        # Validation
        if not username or not password:
            wx.MessageBox('Please enter both username and password',
                          'Error', wx.OK | wx.ICON_ERROR)
            return

        # Show loading cursor
        wx.BeginBusyCursor()

        # Send login request
        payload = {'username': username, 'password': password}
        response = self.send_request('LOGIN', payload)

        # Restore cursor
        wx.EndBusyCursor()

        # Handle response
        if response.get('status') == 'success':
            self.logged_in_username = username
            self.login_success = True
            wx.MessageBox(f'Welcome {username}!',
                          'Login Successful', wx.OK | wx.ICON_INFORMATION)
            # Close the window
            self.Close()
        else:
            error_msg = response.get('message', 'Unknown error')
            wx.MessageBox(f'Login failed: {error_msg}',
                          'Login Failed', wx.OK | wx.ICON_ERROR)
            # Clear password field
            self.password_input.Clear()
            self.password_input.SetFocus()

    def on_forgot_password(self, event):
        """Handle forgot password click"""
        wx.MessageBox('Please contact the administrator to reset your password.',
                      'Forgot Password', wx.OK | wx.ICON_INFORMATION)

    def on_signup_click(self, event):
        """Handle sign up link click - Open Signup window"""
        self.Hide()
        # Import Signup_UI here to avoid circular imports
        try:
            from Signup_UI import SignupFrame
            signup_frame = SignupFrame(self)
            signup_frame.Show()
        except ImportError:
            wx.MessageBox('Signup window not available yet.',
                          'Error', wx.OK | wx.ICON_ERROR)
            self.Show()


# For testing the UI independently
if __name__ == '__main__':
    app = wx.App()
    frame = LoginFrame()
    frame.Show()
    app.MainLoop()

    # After window closes, check result
    if frame.login_success:
        print(f"Login successful! Username: {frame.logged_in_username}")
    else:
        print("Login cancelled or failed")