"""
Gal Haham
Dark-themed user registration window.
Validates passwords, handles admin registration with secret keys,
and communicates with server.
"""
import wx
import socket
import json
from Server.Protocol import Protocol
from Read_server_ip import readServerIp

# --- Configuration ---
HOST = readServerIp()
PORT = 5000
MIN_PASSWORD_LENGTH = 4
USER_ROLE_REGULAR = 0
USER_ROLE_ADMIN = 1


class SignupFrame(wx.Frame):
    """
    Signup window of the app.
    Responsibilities:
    - Display signup form.
    - Validate inputs (password match, length).
    - Support optional admin registration.
    - Send SIGNUP request to server.
    - Return to login screen after success.
    """
    def __init__(self, login_frame=None):
        super().__init__(
            parent=None,
            title='Tennis Social - Sign Up',
            size=(400, 700)
        )

        # Store reference to login frame
        self.login_frame = login_frame

        # Store signup result
        self.signup_success = False

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
        main_sizer.AddSpacer(30)

        # Title
        title = wx.StaticText(panel, label='Create Account')
        title.SetForegroundColour(wx.Colour(255, 255, 255))
        font_title = wx.Font(
            24,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title.SetFont(font_title)
        main_sizer.Add(title, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        # Subtitle
        subtitle = wx.StaticText(panel, label='Join the tennis community')
        subtitle.SetForegroundColour(wx.Colour(153, 153, 153))
        font_subtitle = wx.Font(
            11,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        subtitle.SetFont(font_subtitle)
        main_sizer.Add(subtitle, 0, wx.ALIGN_CENTER | wx.BOTTOM, 30)

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
        self.password_input = wx.TextCtrl(
            panel,
            size=(300, 35),
            style=wx.TE_PASSWORD
        )
        self.password_input.SetBackgroundColour(wx.Colour(26, 26, 26))
        self.password_input.SetForegroundColour(wx.Colour(255, 255, 255))
        form_sizer.Add(self.password_input, 0, wx.EXPAND | wx.BOTTOM, 20)

        # Confirm Password label
        confirm_label = wx.StaticText(panel, label='Confirm Password')
        confirm_label.SetForegroundColour(wx.Colour(204, 204, 204))
        form_sizer.Add(confirm_label, 0, wx.LEFT | wx.BOTTOM, 8)

        # Confirm Password input
        self.confirm_input = wx.TextCtrl(
            panel,
            size=(300, 35),
            style=wx.TE_PASSWORD
        )
        self.confirm_input.SetBackgroundColour(wx.Colour(26, 26, 26))
        self.confirm_input.SetForegroundColour(wx.Colour(255, 255, 255))
        form_sizer.Add(self.confirm_input, 0, wx.EXPAND | wx.BOTTOM, 20)

        # Admin checkbox
        self.admin_checkbox = wx.CheckBox(
            panel,
            label='Register as Admin (requires secret key)'
        )
        self.admin_checkbox.SetForegroundColour(wx.Colour(153, 153, 153))
        self.admin_checkbox.Bind(wx.EVT_CHECKBOX, self.on_admin_check)
        form_sizer.Add(self.admin_checkbox, 0, wx.BOTTOM, 10)

        # Admin secret key label (hidden by default)
        self.secret_label = wx.StaticText(panel, label='Admin Secret Key')
        self.secret_label.SetForegroundColour(wx.Colour(204, 204, 204))
        self.secret_label.Hide()
        form_sizer.Add(self.secret_label, 0, wx.LEFT | wx.BOTTOM, 8)

        # Admin secret key input (hidden by default)
        self.secret_input = wx.TextCtrl(
            panel,
            size=(300, 35),
            style=wx.TE_PASSWORD
        )
        self.secret_input.SetBackgroundColour(wx.Colour(26, 26, 26))
        self.secret_input.SetForegroundColour(wx.Colour(255, 255, 255))
        self.secret_input.Hide()
        form_sizer.Add(self.secret_input, 0, wx.EXPAND | wx.BOTTOM, 20)

        # Sign up button
        self.signup_btn = wx.Button(panel, label='Sign Up', size=(300, 45))
        self.signup_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.signup_btn.SetForegroundColour(wx.Colour(0, 0, 0))
        font_btn = wx.Font(
            12,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        self.signup_btn.SetFont(font_btn)
        self.signup_btn.Bind(wx.EVT_BUTTON, self.on_signup)
        form_sizer.Add(self.signup_btn, 0, wx.EXPAND | wx.BOTTOM, 20)

        # Back to login section
        back_sizer = wx.BoxSizer(wx.HORIZONTAL)
        back_text = wx.StaticText(panel, label="Already have an account? ")
        back_text.SetForegroundColour(wx.Colour(153, 153, 153))
        back_link = wx.StaticText(panel, label='Login')
        back_link.SetForegroundColour(wx.Colour(255, 255, 255))
        back_link.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        back_link.Bind(wx.EVT_LEFT_DOWN, self.on_back_to_login)

        back_sizer.Add(back_text, 0)
        back_sizer.Add(back_link, 0)
        form_sizer.Add(back_sizer, 0, wx.ALIGN_CENTER)

        # Add form to main sizer
        main_sizer.Add(form_sizer, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 50)

        panel.SetSizer(main_sizer)

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
            return {
                "status": "error",
                "message": "Could not connect to server. Is it running?"
            }
        except Exception as e:
            return {"status": "error", "message": f"Network error: {e}"}

    def on_admin_check(self, event):
        """Show/hide admin secret key field"""
        if self.admin_checkbox.GetValue():
            self.secret_label.Show()
            self.secret_input.Show()
        else:
            self.secret_label.Hide()
            self.secret_input.Hide()

        # Refresh layout
        self.Layout()

    def on_signup(self, event):
        """Handle signup button click"""
        username = self.username_input.GetValue().strip()
        password = self.password_input.GetValue().strip()
        confirm = self.confirm_input.GetValue().strip()
        is_admin = (
            USER_ROLE_ADMIN
            if self.admin_checkbox.GetValue()
            else USER_ROLE_REGULAR
        )
        admin_secret = (
            self.secret_input.GetValue().strip()
            if is_admin
            else None
        )

        # Validation
        if not username or not password:
            wx.MessageBox('Please enter username and password',
                          'Error', wx.OK | wx.ICON_ERROR)
            return

        if password != confirm:
            wx.MessageBox('Passwords do not match',
                          'Error', wx.OK | wx.ICON_ERROR)
            self.confirm_input.Clear()
            return

        if len(password) < MIN_PASSWORD_LENGTH:
            wx.MessageBox('Password must be at least 4 characters',
                          'Error', wx.OK | wx.ICON_ERROR)
            return

        # Show loading cursor
        wx.BeginBusyCursor()

        # Prepare payload
        payload = {
            'username': username,
            'password': password,
            'is_admin': is_admin
        }

        if is_admin:
            payload['admin_secret'] = admin_secret

        # Send signup request
        response = self.send_request('SIGNUP', payload)

        # Restore cursor
        wx.EndBusyCursor()

        if response.get('status') == 'success':
            self.signup_success = True
            wx.MessageBox(
                f'Account created successfully!\n'
                f'{response.get("message", "")}\n\n'
                f'Please login with your new account.',
                'Success',
                wx.OK | wx.ICON_INFORMATION
            )
            # Go back to login
            self.on_back_to_login(None)
        else:
            error_msg = response.get('message', 'Unknown error')
            wx.MessageBox(f'Signup failed: {error_msg}',
                          'Signup Failed', wx.OK | wx.ICON_ERROR)

    def on_back_to_login(self, event):
        """Go back to login window"""
        self.Close()
        if self.login_frame:
            self.login_frame.Show()


# For testing the UI independently
if __name__ == '__main__':
    app = wx.App()
    frame = SignupFrame()
    frame.Show()
    app.MainLoop()

    # After window closes, check result
    if frame.signup_success:
        print("Signup successful!")
    else:
        print("Signup cancelled or failed")
