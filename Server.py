import socket       # For network communication
import threading    # To handle multiple clients at once
import sqlite3      # To store users in a local SQLite database
import re           # To validate password format using regex

# Server configuration
IP = "127.0.0.1"              # Localhost (same computer)
PORT = 1730                  # Port number to listen on
DB_FILE = "users.db"         # SQLite database file to store user information
PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*\d).{6,}$"
# Password must have at least one uppercase letter, one digit, and be 6+ characters long


def init_db():
    """
    Create the users table in the database if it doesn't already exist.
    Now includes is_admin field to distinguish between regular and admin users.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        is_admin INTEGER DEFAULT 0)""")
    conn.commit()
    conn.close()


def handle_client(conn, addr):
    """
    Handle communication with a single client.
    This function is run in a separate thread for each connected client.
    """
    print(f"Connected by {addr}")
    with conn:
        while True:
            data = conn.recv(1024).decode()  # Receive data from client
            if not data:
                break  # Connection closed by client

            # Parse the incoming message (supports 4 parts now)
            parts = data.strip().split(" ", 3)

            if len(parts) < 4:
                error_msg = "Invalid request"
                conn.send(error_msg.encode())
                continue

            command, username, password, is_admin_str = parts
            is_admin = int(is_admin_str)

            # Handle signup request
            if command.upper() == "SIGNUP":
                if not re.match(PASSWORD_REGEX, password):
                    error_msg = "Invalid password format."
                    conn.send(error_msg.encode())
                    continue

                response = signup_user(username, password, is_admin)
                conn.send(response.encode())

            # Handle login request
            elif command.upper() == "LOGIN":
                response = login_user(username, password)
                conn.send(response.encode())

            # Handle unknown command
            else:
                response = "Unknown command"
                conn.send(response.encode())


def signup_user(username, password, is_admin):
    """
    Register a new user in the database with an is_admin flag.
    Returns a success message or an error if the username already exists.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                       (username, password, is_admin))
        conn.commit()
        conn.close()
        if is_admin:
            return "Signup successful as admin"
        else:
            return "Signup successful as regular user"
    except sqlite3.IntegrityError:
        return "Username already exists"


def login_user(username, password):
    """
    Check if the username and password match an entry in the database.
    Returns a success or failure message.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return "Login successful" if result else "Login failed"


def start_server():
    """
    Start the server and continuously listen for incoming client connections.
    Each client is handled in a new thread.
    """
    init_db()  # Make sure the database exists
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((IP, PORT))     # Bind the socket to the IP and port
        server.listen()             # Start listening for connections
        print(f"Server listening on {IP}:{PORT}")
        while True:
            conn, addr = server.accept()  # Accept a new client
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


# Run the server when this script is executed directly
if __name__ == "__main__":
    start_server()
