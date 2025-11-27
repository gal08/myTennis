import sqlite3  # Import the SQLite database module.

# DB configuration
DB_NAME = 'users.db'

# ADMIN SECRET KEY - Change this to your own secret!
# In production, this should be in an environment variable or config file
ADMIN_SECRET_KEY = "SecretKey"  # Define the hardcoded admin secret key

ADMIN = 1
ADMIN_STATUS_INDEX = 0
REGULAR_USER_FLAG = 0


# Define the Authentication class for user management.
class Authentication:

    def __init__(self):  # Class constructor
        self._initialize_db()  # Initialize the database upon object creation.

    # Method to ensure the 'users' table exists.
    @staticmethod
    def _initialize_db():
        """Ensures the 'users' table exists."""
        # Connect to the SQLite database.
        conn = sqlite3.connect(DB_NAME)
        # Create a cursor object.
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER NOT NULL
            )
        ''')
        conn.commit()  # Save changes to the database.
        conn.close()  # Close the database connection.

    # Method to check the admin secret key.
    @staticmethod
    def _verify_admin_secret(provided_secret):
        """
        Verifies if the provided admin secret matches the stored secret.
        Returns True if valid, False otherwise.
        """
        if not provided_secret:  # Check if a secret was provided.
            return False  # Return False if none was provided.
        # Return result of secret key comparison.
        return provided_secret == ADMIN_SECRET_KEY

    def signup(self, username, password, is_admin=0, admin_secret=None):
        """
        Registers a new user.
        If is_admin=1, requires valid admin_secret to be provided.
        """
        # Security check: If trying to register as admin, verify the secret
        if is_admin == ADMIN:  # Check if the user attempts to register as admin
            if not self._verify_admin_secret(admin_secret):  # Verify the admin secret.
                return {
                    "status": "error",
                    "message": "Invalid admin secret key. Access denied."
                }

        conn = sqlite3.connect(DB_NAME)  # Connect to the database.
        cursor = conn.cursor()  # Create a cursor.

        try:
            # Insert user with plain text password (as per original code)
            cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                           (username, password, is_admin))
            conn.commit()
            return {
                "status": "success",
                "message": f"Signup successful as {'admin' if is_admin else 'regular user'}"
            }
        except sqlite3.IntegrityError:  # Handle case where username already exists
            return {"status": "error", "message": "Username already exists"}
        finally:
            conn.close()

    @staticmethod
    def login(username, password):
        """Performs login and verification."""
        conn = sqlite3.connect(DB_NAME)  # Connect to the database.
        cursor = conn.cursor()  # Create a cursor.

        # Check username and password
        cursor.execute("SELECT is_admin FROM users WHERE username=? AND password=?", (username, password))
        user_data = cursor.fetchone()  # Fetch the result (is_admin value).
        conn.close()  # Close the database connection.

        if user_data:  # Check if a user was found.
            is_admin = user_data[ADMIN_STATUS_INDEX]  # Extract the admin status.
            return {
                "status": "success",
                "message": "Login successful",
                "is_admin": is_admin
            }

        return {"status": "error", "message": "Invalid username or password."}

    def handle_request(self, request_type, payload):
        """Handles authentication requests from the server."""
        username = payload.get('username')
        password = payload.get('password')
        # Check for missing required fields.
        if not username or not password:
            return {"status": "error", "message": "Missing username or password in request."}

        if request_type == 'SIGNUP':
            # Extract admin flag (default 0)
            is_admin = payload.get('is_admin', REGULAR_USER_FLAG)
            # Extract admin secret
            admin_secret = payload.get('admin_secret', None)
            # Call signup method.
            return self.signup(username, password, is_admin, admin_secret)
        elif request_type == 'LOGIN':
            # Call login method
            return self.login(username, password)

        return {"status": "error", "message": "Unknown authentication request"}
