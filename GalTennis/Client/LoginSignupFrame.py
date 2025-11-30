"""
Gal Haham
Combined login and signup GUI with tabbed interface.
Supports regular and admin user registration with secret key validation.
"""
import wx
USER_ROLE_REGULAR = 0
USER_ROLE_ADMIN = 1


class LoginSignupFrame(wx.Frame):
    """
    GUI window that provides both Login and Signup functionality.

    This frame contains two tabs:
        - Login: Allows existing users to authenticate.
        - Signup: Allows new users to register (regular or admin).

    The frame communicates with the backend via a Client instance
    injected as 'client_instance'. All server interactions
    are performed using client.send_request().
    """

    def __init__(self, client_instance):
        """Initialize the Login/Signup window."""
        super().__init__(
            None,
            title="Tennis Social - Login",
            size=wx.Size(450, 400)
        )
        self.client = client_instance
        self.login_successful = False

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(245, 245, 245))

        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        title_font = wx.Font(
            18,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title = wx.StaticText(panel, label="🎾 Tennis Social")
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(40, 120, 80))
        main_sizer.Add(title, 0, wx.ALL | wx.CENTER, 20)

        # Notebook for tabs
        notebook = wx.Notebook(panel)

        # --- Login Tab ---
        login_panel = wx.Panel(notebook)
        login_sizer = wx.BoxSizer(wx.VERTICAL)

        # Username
        login_sizer.Add(
            wx.StaticText(login_panel, label="Username:"),
            0,
            wx.LEFT | wx.TOP,
            10
        )

        self.login_username = wx.TextCtrl(login_panel, size=wx.Size(300, 30))
        login_sizer.Add(self.login_username, 0, wx.ALL | wx.EXPAND, 10)

        # Password
        login_sizer.Add(
            wx.StaticText(login_panel, label="Password:"),
            0,
            wx.LEFT,
            10
        )

        self.login_password = wx.TextCtrl(
            login_panel,
            size=wx.Size(300, 30),
            style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER
        )

        login_sizer.Add(self.login_password, 0, wx.ALL | wx.EXPAND, 10)

        # Login button
        login_btn = wx.Button(
            login_panel,
            label="Login",
            size=wx.Size(300, 40)
        )

        login_btn.SetBackgroundColour(wx.Colour(76, 175, 80))
        login_btn.SetForegroundColour(wx.WHITE)
        login_btn.Bind(wx.EVT_BUTTON, self.on_login)
        login_sizer.Add(login_btn, 0, wx.ALL | wx.EXPAND, 10)

        # Status label for login
        self.login_status = wx.StaticText(login_panel, label="")
        self.login_status.SetForegroundColour(wx.Colour(200, 0, 0))
        login_sizer.Add(self.login_status, 0, wx.ALL | wx.CENTER, 10)

        login_panel.SetSizer(login_sizer)
        notebook.AddPage(login_panel, "Login")

        # --- Signup Tab ---
        signup_panel = wx.Panel(notebook)
        signup_sizer = wx.BoxSizer(wx.VERTICAL)

        # Username
        signup_sizer.Add(
            wx.StaticText(signup_panel, label="Username:"),
            0,
            wx.LEFT | wx.TOP,
            10
        )

        self.signup_username = wx.TextCtrl(signup_panel, size=wx.Size(300, 30))
        signup_sizer.Add(self.signup_username, 0, wx.ALL | wx.EXPAND, 10)

        # Password
        signup_sizer.Add(
            wx.StaticText(signup_panel, label="Password:"),
            0,
            wx.LEFT,
            10
        )

        self.signup_password = wx.TextCtrl(
            signup_panel,
            size=wx.Size(300, 30),
            style=wx.TE_PASSWORD
        )

        signup_sizer.Add(self.signup_password, 0, wx.ALL | wx.EXPAND, 10)

        # Admin checkbox
        self.admin_checkbox = wx.CheckBox(
            signup_panel,
            label="Register as Manager/Admin"
        )

        signup_sizer.Add(self.admin_checkbox, 0, wx.ALL, 10)

        # Admin secret (initially hidden)
        signup_sizer.Add(
            wx.StaticText(signup_panel, label="Admin Secret Key:"),
            0,
            wx.LEFT,
            10
        )

        self.admin_secret = wx.TextCtrl(
            signup_panel,
            size=wx.Size(300, 30),
            style=wx.TE_PASSWORD
        )

        self.admin_secret.Enable(False)
        signup_sizer.Add(self.admin_secret, 0, wx.ALL | wx.EXPAND, 10)

        # Bind checkbox event
        self.admin_checkbox.Bind(wx.EVT_CHECKBOX, self.on_admin_checkbox)

        # Signup button
        signup_btn = wx.Button(
            signup_panel,
            label="Sign Up",
            size=wx.Size(300, 40)
        )

        signup_btn.SetBackgroundColour(wx.Colour(33, 150, 243))
        signup_btn.SetForegroundColour(wx.WHITE)
        signup_btn.Bind(wx.EVT_BUTTON, self.on_signup)
        signup_sizer.Add(signup_btn, 0, wx.ALL | wx.EXPAND, 10)

        # Status label for signup
        self.signup_status = wx.StaticText(signup_panel, label="")
        self.signup_status.SetForegroundColour(wx.Colour(200, 0, 0))
        signup_sizer.Add(self.signup_status, 0, wx.ALL | wx.CENTER, 10)

        signup_panel.SetSizer(signup_sizer)
        notebook.AddPage(signup_panel, "Sign Up")

        main_sizer.Add(notebook, 1, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(main_sizer)

        self.Centre()
        self.Show()

        # Bind Enter key for login
        self.login_password.Bind(wx.EVT_TEXT_ENTER, self.on_login)

    def on_admin_checkbox(self, event):
        """Enable/disable admin secret field based on checkbox"""
        self.admin_secret.Enable(self.admin_checkbox.GetValue())

    def on_login(self, event):
        """
        Handle the login process:
            - Validate input fields
            - Send LOGIN request to server
            - Update UI based on server response
        """
        username = self.login_username.GetValue().strip()
        password = self.login_password.GetValue().strip()

        if not username or not password:
            self.login_status.SetLabel("Please enter username and password")
            return

        self.login_status.SetLabel("Logging in...")
        self.login_status.SetForegroundColour(wx.Colour(100, 100, 100))
        wx.SafeYield()

        response = self.client._send_request('LOGIN', {
            'username': username,
            'password': password
        })

        if response.get('status') == 'success':
            self.client.username = username

            # Get user admin status
            users_res = self.client._send_request('GET_ALL_USERS', {})
            if users_res.get('users'):
                for user in users_res['users']:
                    if user['username'] == username:
                        self.client.is_admin = user['is_admin']
                        break

            self.login_status.SetLabel("✓ Login successful!")
            self.login_status.SetForegroundColour(wx.Colour(0, 150, 0))
            self.login_successful = True

            wx.CallLater(500, self.Close)
        else:
            self.login_status.SetLabel(
                f"✗ {response.get('message', 'Login failed')}"
            )

            self.login_status.SetForegroundColour(wx.Colour(200, 0, 0))

    def on_signup(self, event):
        """
        Handle account creation:
            - Validate inputs
            - Validate admin secret when needed
            - Send SIGNUP request to server
            - Clear fields on success
        """
        username = self.signup_username.GetValue().strip()
        password = self.signup_password.GetValue().strip()
        is_admin = USER_ROLE_ADMIN \
            if self.admin_checkbox.GetValue() \
            else USER_ROLE_REGULAR

        if not username or not password:
            self.signup_status.SetLabel("Please enter username and password")
            return

        if is_admin and not self.admin_secret.GetValue().strip():
            self.signup_status.SetLabel("Admin secret key required")
            return

        self.signup_status.SetLabel("Creating account...")
        self.signup_status.SetForegroundColour(wx.Colour(100, 100, 100))
        wx.SafeYield()

        payload = {
            'username': username,
            'password': password,
            'is_admin': is_admin
        }

        if is_admin:
            payload['admin_secret'] = self.admin_secret.GetValue().strip()

        response = self.client._send_request('SIGNUP', payload)

        if response.get('status') == 'success':
            self.signup_status.SetLabel("✓ Account created! Please login.")
            self.signup_status.SetForegroundColour(wx.Colour(0, 150, 0))

            # Clear fields
            self.signup_username.SetValue("")
            self.signup_password.SetValue("")
            self.admin_secret.SetValue("")
            self.admin_checkbox.SetValue(False)
            self.admin_secret.Enable(False)
        else:
            self.signup_status.SetLabel(
                f"✗ {response.get('message', 'Signup failed')}"
            )
            self.signup_status.SetForegroundColour(wx.Colour(200, 0, 0))
