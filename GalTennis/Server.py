import sqlite3
from flask import Flask, request, jsonify

# --- Configuration ---
app = Flask(__name__)
DB_FILE = "users.db"
ALLOWED_CATEGORIES = ('forehand', 'backhand', 'serve', 'slice', 'volley', 'smash')
ALLOWED_DIFFICULTIES = ('easy', 'medium', 'hard')


# --- Database Initialization (Server-side) ---
def init_db():
    """Initializes the unified database and creates all necessary tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('forehand', 'backhand', 'serve', 'slice', 'volley', 'smash')),
            difficulty TEXT NOT NULL CHECK(difficulty IN ('easy', 'medium', 'hard'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            username TEXT,
            title TEXT,
            PRIMARY KEY (username, title)
        )
    """)
    conn.commit()
    conn.close()
    print("Database initialized successfully.")


# --- API Routes ---
@app.route('/')
def index():
    return "Server is running OK ✅"


@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin', 0)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                       (username, password, is_admin))
        conn.commit()
        return jsonify(
            {"message": "Signup successful as regular user" if not is_admin else "Admin user registered"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()


@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401


@app.route('/api/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, is_admin FROM users")
    users = [{"username": row[0], "is_admin": bool(row[1])} for row in cursor.fetchall()]
    conn.close()
    return jsonify(users)


@app.route('/api/videos', methods=['POST'])
def add_video():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    title = data.get("title")
    category = data.get("category")
    level = data.get("level")

    if not all([username, password, title, category, level]):
        return jsonify({"error": "Missing fields"}), 400

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        if not cursor.fetchone():
            return jsonify({"error": "Invalid credentials"}), 400

        cursor.execute("INSERT INTO videos (filename, category, difficulty) VALUES (?, ?, ?)",
                       (title, category, level))
        conn.commit()
        return jsonify({"message": "Video added successfully ✅"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/videos', methods=['GET'])
def get_videos():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT filename, category, difficulty FROM videos")
        rows = cursor.fetchall()
        videos = [{"title": r[0], "category": r[1], "level": r[2]} for r in rows]
        return jsonify(videos)
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/like', methods=['POST'])
def like_video():
    data = request.get_json()
    username = data.get('username')
    title = data.get('title')

    if not all([username, title]):
        return jsonify({"error": "Missing data"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO likes (username, title) VALUES (?, ?)", (username, title))
        conn.commit()
        return jsonify({"message": "Video liked successfully"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"message": "You have already liked this video"}), 409
    finally:
        conn.close()


@app.route('/api/likes', methods=['GET'])
def get_likes():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, COUNT(username) as like_count
        FROM likes
        GROUP BY title
    """)
    likes = [{"title": row[0], "likes": row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(likes)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)