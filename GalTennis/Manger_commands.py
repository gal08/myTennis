import sqlite3
import os

# Path to the database file and the folder where video files are stored
VIDEO_DB = "videos.db"
VIDEO_FOLDER = "videos"

# These are the only allowed categories and difficulties for videos
ALLOWED_CATEGORIES = ('forehand', 'backhand', 'serve', 'slice', 'volley', 'smash')
ALLOWED_DIFFICULTIES = ('easy', 'medium', 'hard')

# Manager login credentials
MANAGER_USERNAME = "Gal"
MANAGER_PASSWORD = "Haham2008"

# Ask the manager to enter a username and password.
# Return True if correct, otherwise return False.


def authenticate_manager():
    username = input("Enter manager username: ").strip()
    password = input("Enter manager password: ").strip()
    if username == MANAGER_USERNAME and password == MANAGER_PASSWORD:
        print("Manager authenticated.\n")
        return True
    else:
        print("Invalid username or password.\n")
        return False

# Create the video database if it does not exist yet.
# The table includes: id, filename, category, difficulty.


def init_video_db():
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
    print("Video database initialized successfully.\n")

# Try to add a new video to the database.
# Skip if the file is not .mp4, has invalid category/difficulty, or already exists.



# Go through all the .mp4 files in the videos folder
# Try to extract category and difficulty from the filename
# Then try to add the video to the database


def load_all_videos_from_folder():
    print(f"Scanning folder: {VIDEO_FOLDER}\n")

    # If the folder does not exist, show a message and stop
    if not os.path.exists(VIDEO_FOLDER):
        print(f"Folder '{VIDEO_FOLDER}' does not exist.")
        return

    # Get all the .mp4 files in the folder
    files = os.listdir(VIDEO_FOLDER)
    mp4_files = [f for f in files if f.endswith(".mp4")]

    if not mp4_files:
        print("No .mp4 files found.")
        return

    # Try to add each file to the database
    for filename in mp4_files:
        try:
            name_part = filename[:-4]  # remove .mp4 extension
            category, difficulty, *_ = name_part.split("_")  # extract info from filename
            result = add_video(filename, category.lower(), difficulty.lower())
            print(result)
        except Exception as e:
            print(f"Failed to parse {filename}: {e}")


# Main logic when running the script
if __name__ == "__main__":
    init_video_db()  # create database (if needed)

    if not authenticate_manager():  # ask for manager login
        exit()

    #load_all_videos_from_folder()  # try to add all videos from folder to DB
