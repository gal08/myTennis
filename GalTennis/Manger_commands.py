import sqlite3
import os

# --- Configuration ---
VIDEO_DB = "users.db"
VIDEO_FOLDER = "videos"
ALLOWED_CATEGORIES = ('forehand', 'backhand', 'serve', 'slice', 'volley', 'smash')
ALLOWED_DIFFICULTIES = ('easy', 'medium', 'hard')
MANAGER_USERNAME = "Gal"
MANAGER_PASSWORD = "Hahahm2008"


# --- Functions ---
def authenticate_manager():
    """Authenticates the manager user."""
    username = input("Enter manager username: ").strip()
    password = input("Enter manager password: ").strip()
    return username == MANAGER_USERNAME and password == MANAGER_PASSWORD


def init_video_db():
    """Creates the videos table if it doesn't exist."""
    conn = sqlite3.connect(VIDEO_DB)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN {ALLOWED_CATEGORIES}),
            difficulty TEXT NOT NULL CHECK(difficulty IN {ALLOWED_DIFFICULTIES})
        )
    """)
    conn.commit()
    conn.close()


def add_video(filename, category, difficulty):
    """Adds a single video to the database, preventing duplicates."""
    conn = sqlite3.connect(VIDEO_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM videos WHERE filename = ?", (filename,))
    if cursor.fetchone():
        conn.close()
        return f"Skipped (already exists): {filename}"

    cursor.execute("INSERT INTO videos (filename, category, difficulty) VALUES (?, ?, ?)",
                   (filename, category, difficulty))
    conn.commit()
    conn.close()
    return f"Added: {filename}"


def load_all_videos_from_folder():
    """Loads all videos from the folder into the database."""
    print(f"Scanning folder: {VIDEO_FOLDER}\n")
    if not os.path.exists(VIDEO_FOLDER):
        print(f"Folder '{VIDEO_FOLDER}' does not exist.")
        return

    mp4_files = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith(".mp4")]
    if not mp4_files:
        print("No .mp4 files found.")
        return

    for filename in mp4_files:
        try:
            name_part = filename[:-4]
            category, difficulty, *_ = name_part.split("_")
            result = add_video(filename, category.lower(), difficulty.lower())
            print(result)
        except Exception as e:
            print(f"Failed to parse {filename}: {e}")


# --- Main Logic ---
if __name__ == "__main__":
    if not authenticate_manager():
        print("Authentication failed. Exiting.")
        exit()

    init_video_db()
    load_all_videos_from_folder()