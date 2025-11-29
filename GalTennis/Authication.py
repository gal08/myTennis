import sqlite3
import hashlib

# DB configuration
DB_NAME = 'users.db'

# ADMIN SECRET KEY - Change this to your own secret!
# In production, this should be in an environment variable or config file
ADMIN_SECRET_KEY = "SecretKey"


class Authentication:
    """
    Authentication system that manages user signup and login
    using an SQLite database.

    Responsibilities:
    - Ensure database and tables exist.
    - Support regular and admin account registration.
    - Validate admin secret key before creating admin accounts.
    - Handle login requests and return whether the user is admin.
    """

    def __init__(self):
        """
            Constructor initializes the database on object creation.
        """
        self._initialize_db()

    def _initialize_db(self):
        """Ensures the 'users' table exists."""
        conn = sqlite3.connect(DB_NAME, timeout=10)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def _verify_admin_secret(self, provided_secret):
        """
        Verifies if the provided admin secret matches the stored secret.
        Returns True if valid, False otherwise.
        """
        if not provided_secret:
            return False
        return provided_secret == ADMIN_SECRET_KEY

    def signup(self, username, password, is_admin=0, admin_secret=None):
        """
        Registers a new user.
        If is_admin=1, requires valid admin_secret to be provided.
        """
        # Security check: If trying to register as admin, verify the secret
        if is_admin == 1:
            if not self._verify_admin_secret(admin_secret):
                return {
                    "status": "error",
                    "message": "Invalid admin secret key. Access denied."
                }

        try:
            conn = sqlite3.connect(DB_NAME, timeout=10)
            cursor = conn.cursor()

            try:
                # Insert user with plain text password (as per original code)
                cursor.execute(
                    "INSERT INTO users (username, password, is_admin) "
                    "VALUES (?, ?, ?)",
                    (username, password, is_admin)
                )

                conn.commit()
                return {
                    "status": "success",
                    "message": (
                        f"Signup successful as"
                        f"{'admin' if is_admin else 'regular user'}"
                    )
                }
            except sqlite3.IntegrityError:
                return {
                    "status": "error",
                    "message": "Username already exists"
                }

            finally:
                conn.close()

        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                return {
                    "status": "error",
                    "message": "Database busy, please try again"
                }

            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def login(self, username, password):
        """Performs login and verification."""
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10)
            cursor = conn.cursor()

            # Check username and password
            cursor.execute(
                "SELECT is_admin FROM users "
                "WHERE username=? AND password=?",
                (username, password)
            )

            user_data = cursor.fetchone()
            conn.close()

            if user_data:
                is_admin = user_data[0]
                return {
                    "status": "success",
                    "message": "Login successful",
                    "is_admin": is_admin
                }

            return {
                "status": "error",
                "message": "Invalid username or password."
            }

        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                return {
                    "status": "error",
                    "message": "Database busy, please try again"
                }
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def handle_request(self, request_type, payload):
        """Handles authentication requests from the server."""
        username = payload.get('username')
        password = payload.get('password')

        if not username or not password:
            return {
                "status": "error",
                "message": "Missing username or password in request."
            }

        if request_type == 'SIGNUP':
            is_admin = payload.get('is_admin', 0)
            admin_secret = payload.get('admin_secret', None)
            return self.signup(username, password, is_admin, admin_secret)
        elif request_type == 'LOGIN':
            return self.login(username, password)

        return {"status": "error", "message": "Unknown authentication request"}
