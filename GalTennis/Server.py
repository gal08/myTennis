from flask import Flask, request, jsonify
import sqlite3
import re

# ==== Configuration ====
DB_FILE = "users.db"
PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*\d).{6,}$"  # Password: ≥6 chars, 1 digit, 1 uppercase

app = Flask(__name__)


# ==== Home ====
@app.route('/')
def home():
    return "Server is running OK ✅"


# ==== Database Initialization ====
def init_db():
    """
    Create 'users' and 'videos' tables.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)

    # Videos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            level TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ==== Helper Functions ====
def signup_user(username, password, is_admin):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                       (username, password, is_admin))
        conn.commit()
        conn.close()
        return True, "Signup successful as admin" if is_admin else "Signup successful as regular user"
    except sqlite3.IntegrityError:
        return False, "Username already exists"


def login_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None


# ==== API Routes ====

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    is_admin = int(data.get("is_admin", 0))

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    if not re.match(PASSWORD_REGEX, password):
        return jsonify({"error": "Password must have at least 1 uppercase, 1 digit, 6+ chars"}), 400

    success, message = signup_user(username, password, is_admin)
    status_code = 200 if success else 409
    return jsonify({"message": message}), status_code


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    if login_user(username, password):
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"message": "Login failed"}), 401


@app.route('/api/videos', methods=['POST'])
def add_video():
    """
    Only admin users can add videos.
    JSON input:
    {
        "username": "admin",
        "password": "Admin123",
        "title": "Serve Basics",
        "category": "Serve",
        "level": "Beginner"
    }
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    title = data.get("title")
    category = data.get("category")
    level = data.get("level")

    if not username or not password or not title or not category or not level:
        return jsonify({"error": "Missing fields"}), 400

    # Authenticate and check admin
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"error": "Invalid credentials"}), 401

    is_admin = result[0]
    if not is_admin:
        conn.close()
        return jsonify({"error": "User is not authorized to add videos"}), 403

    # Add video
    cursor.execute("INSERT INTO videos (title, category, level) VALUES (?, ?, ?)",
                   (title, category, level))
    conn.commit()
    conn.close()

    return jsonify({"message": "Video added successfully ✅"}), 201


@app.route('/api/videos', methods=['GET'])
def get_videos():
    """
    Return list of all videos.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT title, category, level FROM videos")
    rows = cursor.fetchall()
    conn.close()

    videos = [{"title": r[0], "category": r[1], "level": r[2]} for r in rows]
    return jsonify(videos)


# ==== Entry Point ====
if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
