"""
Gal Haham
User authentication system with SQLite backend.
Manages signup/login for regular users and admins with secret key validation.
NOW USES DBManager for all database operations.
REFACTORED: Added constants, comprehensive documentation.
"""
from Db_manager import get_db_manager

IS_ADMIN_DEFAULT = 0
ADMIN = 1
REGULAR_USER = 0

USER_ID_INDEX = 0
USERNAME_INDEX = 1
IS_ADMIN_INDEX = 2

# ADMIN SECRET KEY - Change this to your own secret!
# In production, this should be in an environment variable or config file
ADMIN_SECRET_KEY = "SecretKey"

STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

MESSAGE_LOGIN_SUCCESS = "Login successful"
MESSAGE_LOGIN_FAILED = "Invalid username or password."
MESSAGE_ADMIN_SECRET_INVALID = "Invalid admin secret key. Access denied."
MESSAGE_MISSING_CREDENTIALS = "Missing username or password in request."
MESSAGE_UNKNOWN_REQUEST = "Unknown authentication request"

REQUEST_TYPE_SIGNUP = 'SIGNUP'
REQUEST_TYPE_LOGIN = 'LOGIN'

PAYLOAD_KEY_USERNAME = 'username'
PAYLOAD_KEY_PASSWORD = 'password'
PAYLOAD_KEY_IS_ADMIN = 'is_admin'
PAYLOAD_KEY_ADMIN_SECRET = 'admin_secret'


class Authentication:
    """
    Authentication system that manages user signup and login
    using DBManager for database operations.

    Responsibilities:
    - Support regular and admin account registration.
    - Validate admin secret key before creating admin accounts.
    - Handle login requests and return whether the user is admin.

    REFACTORED: Added comprehensive documentation and constants.
    """

    def __init__(self):
        """
        Initialize the authentication system.

        The DBManager is automatically initialized and creates
        the database schema if it doesn't exist.
        """
        self.db = get_db_manager()

    def _verify_admin_secret(self, provided_secret):
        """
        Verify if the provided admin secret matches the stored secret.

        Args:
            provided_secret: The secret key provided by the user

        Returns:
            bool: True if secret is valid, False otherwise
        """
        if not provided_secret:
            return False
        return provided_secret == ADMIN_SECRET_KEY

    def signup(
            self,
            username,
            password,
            is_admin=IS_ADMIN_DEFAULT,
            admin_secret=None
    ):
        """
        Register a new user in the system.

        If registering as admin (is_admin=1), requires a valid admin_secret.
        Regular users can sign up without providing admin_secret.

        Args:
            username: Username for the new account
            password: Password for the new account
            is_admin: 1 for admin, 0 for regular user (default: 0)
            admin_secret: Required if is_admin=1, must match ADMIN_SECRET_KEY

        Returns:
            dict: Response with status and message
                - status: "success" or "error"
                - message: Description of the result
        """
        # Security check: If trying to register as admin, verify the secret
        if is_admin == ADMIN:
            if not self._verify_admin_secret(admin_secret):
                return self._create_error_response(
                    MESSAGE_ADMIN_SECRET_INVALID,
                )
        # Use DBManager to create user
        return self.db.create_user(username, password, is_admin)

    def login(self, username, password):
        """
        Perform user login and verification.

        Args:
            username: Username to authenticate
            password: Password to verify

        Returns:
            dict: Response with status, message, and is_admin flag
                - status: "success" or "error"
                - message: Description of the result
                - is_admin: (only on success) 1 if admin, 0 if regular user
        """
        user_data = self.db.get_user(username, password)

        if user_data:
            # user_data is tuple: (id, username, is_admin)
            is_admin = user_data[IS_ADMIN_INDEX]
            return self._create_login_success_response(is_admin)

        return self._create_error_response(MESSAGE_LOGIN_FAILED)

    def handle_request(self, request_type, payload):
        """
        Handle authentication requests from the server.

        Routes requests to appropriate handlers (signup/login) based on type.

        Args:
            request_type: Type of request ('SIGNUP' or 'LOGIN')
            payload: Dictionary containing request data
                - username: Required
                - password: Required
                - is_admin: Optional, for SIGNUP (default: 0)
                - admin_secret: Optional, for SIGNUP as admin

        Returns:
            dict: Response from signup() or login() method
        """
        # Extract credentials
        username = payload.get(PAYLOAD_KEY_USERNAME)
        password = payload.get(PAYLOAD_KEY_PASSWORD)

        # Validate credentials present
        if not username or not password:
            return self._create_error_response(MESSAGE_MISSING_CREDENTIALS)

        # Route to appropriate handler
        if request_type == REQUEST_TYPE_SIGNUP:
            return self._handle_signup_request(payload, username, password)
        elif request_type == REQUEST_TYPE_LOGIN:
            return self.login(username, password)

        return self._create_error_response(MESSAGE_UNKNOWN_REQUEST)

    def _handle_signup_request(self, payload, username, password):
        """
        Handle signup request with extracted credentials.

        Args:
            payload: Original payload dictionary
            username: Extracted username
            password: Extracted password

        Returns:
            dict: Response from signup() method
        """
        is_admin = payload.get(PAYLOAD_KEY_IS_ADMIN, IS_ADMIN_DEFAULT)
        admin_secret = payload.get(PAYLOAD_KEY_ADMIN_SECRET, None)
        return self.signup(username, password, is_admin, admin_secret)

    def _create_error_response(self, message):
        """
        Create a standardized error response.

        Args:
            message: Error message to include

        Returns:
            dict: Error response dictionary
        """
        return {
            "status": STATUS_ERROR,
            "message": message
        }

    def _create_login_success_response(self, is_admin):
        """
        Create a successful login response.

        Args:
            is_admin: Admin status of the user (0 or 1)

        Returns:
            dict: Success response with admin status
        """
        return {
            "status": STATUS_SUCCESS,
            "message": MESSAGE_LOGIN_SUCCESS,
            "is_admin": is_admin
        }
