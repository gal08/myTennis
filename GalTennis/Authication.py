import sqlite3

# DB configuration (Ensure the file name matches other files)
DB_NAME = 'users.db'


class Authentication:

    def __init__(self):
        self._initialize_db()

    def _initialize_db(self):
        """Ensures the 'users' table exists."""
        conn = sqlite3.connect(DB_NAME)
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

    def signup(self, username, password, is_admin=0):
        """Registers a new user."""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:
            # Inserting the password as plain text (as in the original Flask code)
            cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                           (username, password, is_admin))
            conn.commit()
            return {"status": "success", "message": f"Signup successful as {'admin' if is_admin else 'regular user'}"}
        except sqlite3.IntegrityError:
            # Error handling: Username already exists
            return {"status": "error", "message": "Username already exists"}
        finally:
            conn.close()

    def login(self, username, password):
        """Performs login and verification."""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Check username and password as plain text
        cursor.execute("SELECT is_admin FROM users WHERE username=? AND password=?", (username, password))
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            is_admin = user_data[0]
            return {"status": "success", "message": "Login successful", "is_admin": is_admin}

        # Error handling: Incorrect password / User does not exist
        return {"status": "error", "message": "Invalid username or password."}

    # Method to unify logic for use by the Server
    def handle_request(self, request_type, payload):
        username = payload.get('username')
        password = payload.get('password')

        if not username or not password:
            return {"status": "error", "message": "Missing username or password in request."}

        if request_type == 'SIGNUP':
            # is_admin defaults to 0 as per your original Flask code
            return self.signup(username, password, payload.get('is_admin', 0))
        elif request_type == 'LOGIN':
            return self.login(username, password)

        return {"status": "error", "message": "Unknown authentication request"}
