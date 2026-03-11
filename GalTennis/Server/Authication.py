"""
Gal Haham
User authentication system with SQLite backend.
Manages signup/login for regular users.
NOW USES DBManager for all database operations.
REFACTORED: Added constants, comprehensive documentation.
"""
from Db_manager import get_db_manager

USER_ID_INDEX = 0
USERNAME_INDEX = 1
PASSWORD_INDEX = 2

STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

MESSAGE_LOGIN_SUCCESS = "Login successful"
MESSAGE_LOGIN_FAILED = "Invalid username or password."
MESSAGE_MISSING_CREDENTIALS = "Missing username or password in request."
MESSAGE_UNKNOWN_REQUEST = "Unknown authentication request"

REQUEST_TYPE_SIGNUP = 'SIGNUP'
REQUEST_TYPE_LOGIN = 'LOGIN'

PAYLOAD_KEY_USERNAME = 'username'
PAYLOAD_KEY_PASSWORD = 'password'


class Authentication:
    """
    Authentication system that manages user signup and login
    using DBManager for database operations.

    Responsibilities:
    - Support regular user registration.
    - Handle login requests.

    REFACTORED: Added comprehensive documentation and constants.
    """

    def __init__(self):
        """
        Initialize the authentication system.

        The DBManager is automatically initialized and creates
        the database schema if it doesn't exist.
        """
        self.db = get_db_manager()

    def signup(self, username, password):
        """
        Register a new user in the system.
        """
        print("SIGNUP REQUEST:", repr(username), repr(password))

        result = self.db.create_user(username, password)
        print("SIGNUP RESULT:", result)
        print("USERS IN DB NOW:", self.db.get_all_users())

        return result

    def login(self, username, password):
        """
        Perform user login and verification.

        Args:
            username: Username to authenticate
            password: Password to verify

        Returns:
            dict: Response with status and message
                - status: "success" or "error"
                - message: Description of the result
        """
        user_data = self.db.get_user(username, password)

        if user_data:
            return self._create_login_success_response()

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

        Returns:
            dict: Response from signup() or login() method
        """
        username = payload.get(PAYLOAD_KEY_USERNAME)
        password = payload.get(PAYLOAD_KEY_PASSWORD)

        if not username or not password:
            return self._create_error_response(MESSAGE_MISSING_CREDENTIALS)

        if request_type == REQUEST_TYPE_SIGNUP:
            return self.signup(username, password)
        elif request_type == REQUEST_TYPE_LOGIN:
            return self.login(username, password)

        return self._create_error_response(MESSAGE_UNKNOWN_REQUEST)

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

    def _create_login_success_response(self):
        """
        Create a successful login response.

        Returns:
            dict: Success response
        """
        return {
            "status": STATUS_SUCCESS,
            "message": MESSAGE_LOGIN_SUCCESS
        }