"""
Gal Haham
Combined login and signup GUI with tabbed interface.
Supports regular user registration.
"""
import wx
import hashlib

# Window Configuration
WINDOW_WIDTH = 450
WINDOW_HEIGHT = 400
WINDOW_TITLE = "Tennis Social - Login"

# Colors
COLOR_BACKGROUND = wx.Colour(245, 245, 245)
COLOR_TITLE = wx.Colour(40, 120, 80)
COLOR_SUCCESS = wx.Colour(0, 150, 0)
COLOR_ERROR = wx.Colour(200, 0, 0)
COLOR_PROGRESS = wx.Colour(100, 100, 100)
COLOR_LOGIN_BUTTON = wx.Colour(76, 175, 80)
COLOR_SIGNUP_BUTTON = wx.Colour(33, 150, 243)
COLOR_WHITE = wx.WHITE

# Fonts
FONT_SIZE_TITLE = 18

# Widget Sizes
FIELD_WIDTH = 300
FIELD_HEIGHT = 30
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 40

# Spacing
SPACING_TITLE_ALL = 20
SPACING_NOTEBOOK = 10
SPACING_FIELD_LEFT_TOP = 10
SPACING_FIELD_LEFT = 10
SPACING_FIELD_ALL = 10
SPACING_STATUS = 10

# Timing
LOGIN_CLOSE_DELAY_MS = 500


class LoginSignupFrame(wx.Frame):
    """
    GUI window that provides both Login and Signup functionality.

    This frame contains two tabs:
        - Login: Allows existing users to authenticate.
        - Signup: Allows new users to register.

    The frame communicates with the backend via a Client instance
    injected as 'client_instance'. All server interactions
    are performed using client._send_request().
    """

    def __init__(self, client_instance):
        """Initialize the Login/Signup window."""
        super().__init__(
            None,
            title=WINDOW_TITLE,
            size=wx.Size(WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        self.client = client_instance
        self.login_successful = False

        panel = self._create_main_panel()
        main_sizer = self._build_ui_structure(panel)
        self._finalize_setup(panel, main_sizer)

    def _create_main_panel(self):
        """Create and configure the main panel."""
        panel = wx.Panel(self)
        panel.SetBackgroundColour(COLOR_BACKGROUND)
        return panel

    def _build_ui_structure(self, panel):
        """Build the complete UI structure and return main sizer."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self._add_title(panel, main_sizer)
        notebook = self._create_notebook(panel)
        main_sizer.Add(notebook, 1, wx.ALL | wx.EXPAND, SPACING_NOTEBOOK)
        return main_sizer

    def _add_title(self, panel, sizer):
        """Add the application title to the panel."""
        title_font = wx.Font(
            FONT_SIZE_TITLE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )
        title = wx.StaticText(panel, label="Tennis Social")
        title.SetFont(title_font)
        title.SetForegroundColour(COLOR_TITLE)
        sizer.Add(title, 0, wx.ALL | wx.CENTER, SPACING_TITLE_ALL)

    def _create_notebook(self, panel):
        """Create notebook with login and signup tabs."""
        notebook = wx.Notebook(panel)
        login_panel = self._create_login_tab(notebook)
        signup_panel = self._create_signup_tab(notebook)
        notebook.AddPage(login_panel, "Login")
        notebook.AddPage(signup_panel, "Sign Up")
        return notebook

    def _create_login_tab(self, notebook):
        """Create the login tab with all its components."""
        login_panel = wx.Panel(notebook)
        login_sizer = wx.BoxSizer(wx.VERTICAL)
        self._add_login_username_field(login_panel, login_sizer)
        self._add_login_password_field(login_panel, login_sizer)
        self._add_login_button(login_panel, login_sizer)
        self._add_login_status_label(login_panel, login_sizer)
        login_panel.SetSizer(login_sizer)
        return login_panel

    def _add_login_username_field(self, panel, sizer):
        """Add username field to login tab."""
        sizer.Add(
            wx.StaticText(panel, label="Username:"),
            0,
            wx.LEFT | wx.TOP,
            SPACING_FIELD_LEFT_TOP
        )
        self.login_username = wx.TextCtrl(
            panel,
            size=wx.Size(FIELD_WIDTH, FIELD_HEIGHT),
        )
        sizer.Add(self.login_username, 0, wx.ALL | wx.EXPAND, SPACING_FIELD_ALL)

    def _add_login_password_field(self, panel, sizer):
        """Add password field to login tab."""
        sizer.Add(
            wx.StaticText(panel, label="Password:"),
            0,
            wx.LEFT,
            SPACING_FIELD_LEFT
        )
        self.login_password = wx.TextCtrl(
            panel,
            size=wx.Size(FIELD_WIDTH, FIELD_HEIGHT),
            style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER
        )
        sizer.Add(self.login_password, 0, wx.ALL | wx.EXPAND, SPACING_FIELD_ALL)

    def _add_login_button(self, panel, sizer):
        """Add login button to login tab."""
        login_btn = wx.Button(
            panel,
            label="Login",
            size=wx.Size(BUTTON_WIDTH, BUTTON_HEIGHT)
        )
        login_btn.SetBackgroundColour(COLOR_LOGIN_BUTTON)
        login_btn.SetForegroundColour(COLOR_WHITE)
        login_btn.Bind(wx.EVT_BUTTON, self.on_login)
        sizer.Add(login_btn, 0, wx.ALL | wx.EXPAND, SPACING_FIELD_ALL)

    def _add_login_status_label(self, panel, sizer):
        """Add status label to login tab."""
        self.login_status = wx.StaticText(panel, label="")
        self.login_status.SetForegroundColour(COLOR_ERROR)
        sizer.Add(self.login_status, 0, wx.ALL | wx.CENTER, SPACING_STATUS)

    def _create_signup_tab(self, notebook):
        """Create the signup tab with all its components."""
        signup_panel = wx.Panel(notebook)
        signup_sizer = wx.BoxSizer(wx.VERTICAL)
        self._add_signup_username_field(signup_panel, signup_sizer)
        self._add_signup_password_field(signup_panel, signup_sizer)
        self._add_signup_button(signup_panel, signup_sizer)
        self._add_signup_status_label(signup_panel, signup_sizer)
        signup_panel.SetSizer(signup_sizer)
        return signup_panel

    def _add_signup_username_field(self, panel, sizer):
        """Add username field to signup tab."""
        sizer.Add(
            wx.StaticText(panel, label="Username:"),
            0,
            wx.LEFT | wx.TOP,
            SPACING_FIELD_LEFT_TOP
        )
        self.signup_username = wx.TextCtrl(
            panel,
            size=wx.Size(FIELD_WIDTH, FIELD_HEIGHT),
        )
        sizer.Add(self.signup_username, 0, wx.ALL | wx.EXPAND, SPACING_FIELD_ALL)

    def _add_signup_password_field(self, panel, sizer):
        """Add password field to signup tab."""
        sizer.Add(
            wx.StaticText(panel, label="Password:"),
            0,
            wx.LEFT,
            SPACING_FIELD_LEFT
        )
        self.signup_password = wx.TextCtrl(
            panel,
            size=wx.Size(FIELD_WIDTH, FIELD_HEIGHT),
            style=wx.TE_PASSWORD
        )
        sizer.Add(self.signup_password, 0, wx.ALL | wx.EXPAND, SPACING_FIELD_ALL)

    def _add_signup_button(self, panel, sizer):
        """Add signup button to signup tab."""
        signup_btn = wx.Button(
            panel,
            label="Sign Up",
            size=wx.Size(BUTTON_WIDTH, BUTTON_HEIGHT)
        )
        signup_btn.SetBackgroundColour(COLOR_SIGNUP_BUTTON)
        signup_btn.SetForegroundColour(COLOR_WHITE)
        signup_btn.Bind(wx.EVT_BUTTON, self.on_signup)
        sizer.Add(signup_btn, 0, wx.ALL | wx.EXPAND, SPACING_FIELD_ALL)

    def _add_signup_status_label(self, panel, sizer):
        """Add status label to signup tab."""
        self.signup_status = wx.StaticText(panel, label="")
        self.signup_status.SetForegroundColour(COLOR_ERROR)
        sizer.Add(self.signup_status, 0, wx.ALL | wx.CENTER, SPACING_STATUS)

    def _finalize_setup(self, panel, main_sizer):
        """Finalize window setup."""
        panel.SetSizer(main_sizer)
        self.Centre()
        self.Show()
        self.login_password.Bind(wx.EVT_TEXT_ENTER, self.on_login)

    def on_login(self, event):
        """
        Handle the login process.

        Args:
            event: wx.Event from button or Enter key
        """
        credentials = self._get_login_credentials()
        if not credentials:
            return

        self._show_login_progress()
        response = self._send_login_request(credentials)

        if response.get('status') == 'success':
            self._handle_login_success(credentials['username'])
        else:
            self._handle_login_failure(response)

    def _get_login_credentials(self):
        """
        Get and validate login credentials.

        Returns:
            dict: Credentials dict or None if validation fails
        """
        username = self.login_username.GetValue().strip()
        password = self.login_password.GetValue().strip()
        hashed_pwd = hashlib.sha256(password.encode()).hexdigest()

        if not username or not password:
            self.login_status.SetLabel("Please enter username and password")
            return None

        return {'username': username, 'password': hashed_pwd}

    def _show_login_progress(self):
        """Show login progress indicator."""
        self.login_status.SetLabel("Logging in...")
        self.login_status.SetForegroundColour(COLOR_PROGRESS)
        wx.SafeYield()

    def _send_login_request(self, credentials):
        """
        Send login request to server.

        Args:
            credentials: Dict with username and password

        Returns:
            dict: Server response
        """
        return self.client._send_request('LOGIN', {
            'username': credentials['username'],
            'password': credentials['password']
        })

    def _handle_login_success(self, username):
        """
        Handle successful login.

        Args:
            username: Logged in username
        """
        self.client.username = username
        self.login_status.SetLabel("Login successful!")
        self.login_status.SetForegroundColour(COLOR_SUCCESS)
        self.login_successful = True
        wx.CallLater(LOGIN_CLOSE_DELAY_MS, self.Close)

    def _handle_login_failure(self, response):
        """
        Handle failed login.

        Args:
            response: Server response dict
        """
        error_message = response.get('message', 'Login failed')
        self.login_status.SetLabel(f"{error_message}")
        self.login_status.SetForegroundColour(COLOR_ERROR)

    def on_signup(self, event):
        """
        Handle account creation.

        Args:
            event: wx.Event from button
        """
        signup_data = self._get_signup_input()
        if not signup_data:
            return

        self._show_signup_progress()
        response = self._send_signup_request(signup_data)
        self._handle_signup_response(response)

    def _get_signup_input(self):
        """
        Get and validate basic signup input.

        Returns:
            dict: Signup data or None if validation fails
        """
        username = self.signup_username.GetValue().strip()
        password = self.signup_password.GetValue().strip()
        hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
        if not username or not password:
            self.signup_status.SetLabel("Please enter username and password")
            return None

        return {'username': username, 'password': hashed_pwd}

    def _show_signup_progress(self):
        """Display progress indicator during signup."""
        self.signup_status.SetLabel("Creating account...")
        self.signup_status.SetForegroundColour(COLOR_PROGRESS)
        wx.SafeYield()

    def _send_signup_request(self, signup_data):
        """
        Build and send signup request to server.

        Args:
            signup_data: Dict with signup information

        Returns:
            dict: Server response
        """
        payload = {
            'username': signup_data['username'],
            'password': signup_data['password']
        }
        print("CLIENT SEND SIGNUP TO:", self.client.host, self.client.port)
        return self.client._send_request('SIGNUP', payload)

    def _handle_signup_response(self, response):
        """
        Handle server response to signup request.

        Args:
            response: Server response dict
        """
        if response.get('status') == 'success':
            self._handle_signup_success()
        else:
            self._handle_signup_failure(response)

    def _handle_signup_success(self):
        """Handle successful signup - update UI and clear fields."""
        self.signup_status.SetLabel("Account created! Please login.")
        self.signup_status.SetForegroundColour(COLOR_SUCCESS)
        self._clear_signup_fields()

    def _handle_signup_failure(self, response):
        """
        Handle failed signup - display error message.

        Args:
            response: Server response dict
        """
        error_message = response.get('message', 'Signup failed')
        self.signup_status.SetLabel(f"{error_message}")
        self.signup_status.SetForegroundColour(COLOR_ERROR)

    def _clear_signup_fields(self):
        """Clear all signup form fields."""
        self.signup_username.SetValue("")
        self.signup_password.SetValue("")