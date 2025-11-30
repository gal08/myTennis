"""
Gal Haham
Video metadata management system.
Handles video upload registration and retrieval
with category/difficulty validation.
"""
import sqlite3
import time  # MUST be imported for generating timestamp

TITLE_INDEX = 0
UPLOADER_INDEX = 1
CATEGORY_INDEX = 2
LEVEL_INDEX = 3
TIMESTAMP_INDEX = 4

# DB configuration
DB_NAME = 'users.db'
ALLOWED_CATEGORIES = (
    'forehand', 'backhand', 'serve',
    'slice', 'volley', 'smash'
)
ALLOWED_DIFFICULTIES = ('easy', 'medium', 'hard')


class VideosHandler:
    """
    Class for managing video content: adding and retrieving the video list.
    Handles 'ADD_VIDEO' and 'GET_VIDEOS' requests.
    """

    def __init__(self):
        self._initialize_db()

    def _initialize_db(self):
        """Ensures the 'videos' table exists with all required
        fields (uploader, timestamp, UNIQUE filename)."""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Updated table structure
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                uploader TEXT NOT NULL,
                category TEXT NOT NULL
                    CHECK(category IN (
                        'forehand','backhand','serve','slice','volley','smash'
                    )),
                difficulty TEXT NOT NULL
                    CHECK(difficulty IN ('easy','medium','hard')),
                timestamp REAL NOT NULL
            )
            """
        )

        conn.commit()
        conn.close()

    def add_video(self, payload):
        """
        Adds a new video record to the DB.
        """
        title = payload.get("title")
        category = payload.get("category")
        level = payload.get("level")
        uploader = payload.get("uploader")  # Essential for tracking the user

        if not all([title, category, level, uploader]):
            return {
                "status": "error",
                "message": (
                    "Missing video title, category, "
                    "level, or uploader in request."
                )
            }

        if (
                category not in ALLOWED_CATEGORIES or
                level not in ALLOWED_DIFFICULTIES
        ):
            return {
                "status": "error",
                "message": "Invalid category or difficulty level."
            }

        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            current_time = time.time()

            cursor.execute(
                "INSERT INTO videos (filename, "
                "uploader, "
                "category, "
                "difficulty, "
                "timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    title,
                    uploader,
                    category,
                    level,
                    current_time
                )
            )

            conn.commit()
            return {
                "status": "success",
                "message": "Video metadata added successfully"
            }

        except sqlite3.IntegrityError:
            return {
                "status": "error",
                "message": (
                    "The video title already exists. "
                    "Please choose a unique title."
                )
            }

        except Exception as e:
            return {
                "status": "error",
                "message": (
                    f"DB Error while adding video: {e}"
                )
            }

        finally:
            if conn:
                conn.close()

    def get_videos(self):
        """Retrieves all available videos,
         ordered by latest upload (timestamp)."""
        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Fetching all required fields, ordered by timestamp (newest first)
            cursor.execute(
                "SELECT filename, uploader, category, difficulty, timestamp "
                "FROM videos "
                "ORDER BY timestamp DESC"
            )
            rows = cursor.fetchall()

            # Formatting output to match the client's expected keys
            videos = [{
                "title": r[TITLE_INDEX],
                "uploader": r[UPLOADER_INDEX],
                "category": r[CATEGORY_INDEX],
                "level": r[LEVEL_INDEX],
                "timestamp": r[TIMESTAMP_INDEX]
            } for r in rows]

            return {"status": "success", "videos": videos}
        except sqlite3.Error as e:
            return {"status": "error", "message": f"Database error: {e}"}
        finally:
            if conn:
                conn.close()

    # Method that unifies the logic for use by the Server
    def handle_request(self, request_type, payload):
        if request_type == 'ADD_VIDEO':
            return self.add_video(payload)
        elif request_type == 'GET_VIDEOS':
            return self.get_videos()

        return {"status": "error", "message": "Unknown video request"}
