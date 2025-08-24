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


@app.route('/api/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, is_admin FROM users")
    rows = cursor.fetchall()
    conn.close()

    users = [
        {"username": r[0], "password": r[1], "is_admin": bool(r[2])}
        for r in rows
    ]
    return jsonify(users)


# ==== Database Initialization ====
def init_db():
    """
    Create 'users', 'videos', and 'likes' tables.
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

    # Likes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            username TEXT,
            title TEXT,
            PRIMARY KEY (username, title),
            FOREIGN KEY (username) REFERENCES users(username),
            FOREIGN KEY (title) REFERENCES videos(title)
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
    status_code = 200 if success else 400
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
        return jsonify({"message": "Login failed"}), 400


@app.route('/api/videos', methods=['POST'])
def add_video():
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
        return jsonify({"error": "Invalid credentials"}), 400

    is_admin = result[0]
    if not is_admin:
        conn.close()
        return jsonify({"error": "User is not authorized to add videos"}), 400

    # Add video
    cursor.execute("INSERT INTO videos (title, category, level) VALUES (?, ?, ?)",
                   (title, category, level))
    conn.commit()
    conn.close()

    return jsonify({"message": "Video added successfully ✅"}), 200


@app.route('/api/videos', methods=['GET'])
def get_videos():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT title, category, level FROM videos")
    rows = cursor.fetchall()
    conn.close()

    videos = [{"title": r[0], "category": r[1], "level": r[2]} for r in rows]
    return jsonify(videos)


@app.route('/api/like', methods=['POST'])
def like_video():
    data = request.get_json()
    username = data.get("username")
    title = data.get("title")

    if not username or not title:
        return jsonify({"error": "Missing username or title"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # check if user exists
    cursor.execute("SELECT 1 FROM users WHERE username=?", (username,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "User does not exist"}), 400

    # check if video exists
    cursor.execute("SELECT 1 FROM videos WHERE title=?", (title,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Video does not exist"}), 400

    try:
        cursor.execute("INSERT INTO likes (username, title) VALUES (?, ?)", (username, title))
        conn.commit()
        conn.close()
        return jsonify({"message": "Liked successfully ❤️"}), 200
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"message": "Already liked"}), 200


@app.route('/api/likes', methods=['GET'])
def get_likes():
    """
    Returns number of likes per video
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, COUNT(*) as like_count
        FROM likes
        GROUP BY title
    """)
    rows = cursor.fetchall()
    conn.close()

    results = [{"title": r[0], "likes": r[1]} for r in rows]
    return jsonify(results)


# ==== Entry Point ====
if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
