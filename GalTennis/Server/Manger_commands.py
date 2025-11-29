import sqlite3

# DB configuration - Standardized name
DB_NAME = 'users.db'
USER_COL_USERNAME = 0
USER_COL_IS_ADMIN = 1


# NOTE: The constants below are used for reference in this handler
ALLOWED_CATEGORIES = (
    'forehand',
    'backhand',
    'serve',
    'slice',
    'volley',
    'smash'
)

ALLOWED_DIFFICULTIES = ('easy', 'medium', 'hard')


class ManagerCommands:
    """
    Handles commands requiring manager/admin privileges.
    Currently supports: GET_ALL_USERS.
    """

    def __init__(self):
        # Initialize the DB connection using the standardized name
        self._initialize_db()

    @staticmethod
    def _initialize_db():
        """
        Ensures the database file exists and is accessible.
        Note: The actual table creation for 'users' and
        'videos' is handled by their respective Handlers.
        """
        try:
            conn = sqlite3.connect(DB_NAME)
            # Just opening and closing to verify connection access
            conn.close()
        except sqlite3.Error as e:
            print(f"Error initializing ManagerCommands DB connection: {e}")

    @staticmethod
    def get_all_users(payload):
        """
        Retrieves a list of all users and their admin status.
        NOTE: Server.py enforces the admin check before calling this method.
        """
        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Retrieve username and admin status, but NOT the password hash
            cursor.execute(
                "SELECT username, is_admin FROM users ORDER BY username ASC"
            )

            users_data = cursor.fetchall()

            users = [
                {
                    "username": row[USER_COL_USERNAME],
                    "is_admin": row[USER_COL_IS_ADMIN]
                }
                for row in users_data
            ]

            return {"status": "success", "users": users}

        except sqlite3.Error as e:
            return {
                "status": "error",
                "message": f"Database error during user retrieval: {e}"
            }

        finally:
            if conn:
                conn.close()

    def handle_request(self, request_type, payload):
        """Routes the manager request to the appropriate method."""
        if request_type == 'GET_ALL_USERS':
            """Admin check must happen at the Server.py level,
             but we proceed with DB fetch"""
            return self.get_all_users(payload)
        else:
            return {
                "status": "error",
                "message": "Unknown manager command type."
            }
