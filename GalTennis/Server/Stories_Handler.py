"""
Gal Haham
Story management system with 24-hour expiration.
Handles story creation, retrieval, and automatic cleanup of expired content.
"""
import sqlite3
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

STORIES_FOLDER = "stories"

STORY_FOLDER = "stories"


# DB configuration
DB_NAME = 'users.db'
FIRST_PART_INDEX = 0
MIN_PARTS_WITH_SEPARATOR = 1
HOURS_IN_A_DAY = 24
USERNAME_INDEX = 0
CONTENT_TYPE_INDEX = 1
CONTENT_INDEX = 2
FILENAME_INDEX = 3
TIMESTAMP_INDEX = 4
ID_INDEX = 5
FILE_EXTENSION_INDEX = 1
COLUMN_TYPE_INDEX = 1


class StoriesHandler:
    """
    Handles ADD_STORY and GET_STORIES operations
    with support for text, images, and videos.
    Stories expire after 24 hours.
    """

    def __init__(self):
        self._ensure_stories_folder()
        self._initialize_db()

    def _ensure_stories_folder(self):
        """Creates the stories folder if it doesn't exist."""
        if not os.path.exists(STORIES_FOLDER):
            os.makedirs(STORIES_FOLDER)

    def _initialize_db(self):
        """Ensures the 'stories' table exists with
        support for different content types."""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='stories'
        """)
        table_exists = cursor.fetchone()

        if not table_exists:
            # Create new table with all columns
            cursor.execute("""
                CREATE TABLE stories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    content_type TEXT NOT NULL
                    DEFAULT 'text'
                    CHECK(content_type IN ('text', 'image', 'video')),
                    content TEXT NOT NULL,
                    filename TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            print("Stories table created with media support.")
        else:
            # Ensure columns exist
            cursor.execute("PRAGMA table_info(stories)")
            columns = [
                column[COLUMN_TYPE_INDEX]
                for column in cursor.fetchall()
            ]

            if 'content_type' not in columns:
                print(
                    "ERROR: stories table missing content_type column. "
                    "Please migrate manually."
                )

            if 'filename' not in columns:
                cursor.execute("ALTER TABLE stories ADD COLUMN filename TEXT")
                print("Added filename column to stories table")

        conn.commit()
        conn.close()

    def add_story(self, payload):
        """
        Adds a new story to the database.
        Expected payload:
            {
                'username': 'user1',
                'filename': 'story.mp4',
                'content_type': 'photo'|'video'
            }
        """
        username = payload.get('username')
        filename = payload.get('filename')
        content_type = payload.get('content_type', 'photo')

        if not username or not filename:
            return {
                "status": "error",
                "message": "Missing username or filename"
            }

        timestamp = int(time.time())
        ext = os.path.splitext(filename)[FILE_EXTENSION_INDEX]
        unique_filename = f"{username}_{timestamp}{ext}"

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            current_time = time.strftime("%Y-%m-%d %H:%M:%S")

            sql_insert = """
                INSERT INTO stories (
                    username,
                    content_type,
                    content,
                    filename,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(
                sql_insert,
                (
                    username,
                    content_type,
                    filename,
                    unique_filename,
                    current_time,
                )
            )

            conn.commit()
            conn.close()

            return {
                "status": "success",
                "message": "Story registered successfully!",
                "unique_filename": unique_filename
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Database error: {e}"
            }

    def get_stories(self, payload):
        """
        Retrieves all stories from the last 24 hours.
        Returns file paths for image/video stories.
        """
        twenty_four_hours_ago = (
                datetime.now() -
                timedelta(hours=HOURS_IN_A_DAY)
        ).strftime("%Y-%m-%d %H:%M:%S")

        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT username, content_type, content, filename, timestamp, id
                FROM stories
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (twenty_four_hours_ago,))

            rows = cursor.fetchall()

            stories = []
            for row in rows:
                story = {
                    "username": row[USERNAME_INDEX],
                    "content_type": row[CONTENT_TYPE_INDEX],
                    "content": row[CONTENT_INDEX],
                    "filename": row[FILENAME_INDEX],
                    "timestamp": row[TIMESTAMP_INDEX],
                    "id": row[ID_INDEX],
                }

                # Add file path for media
                if story["content_type"] in ['image', 'video']:
                    media_path = os.path.join(STORIES_FOLDER, story["content"])
                    if os.path.exists(media_path):
                        story["file_path"] = media_path
                    else:
                        story["file_path"] = None

                stories.append(story)

            return {"status": "success", "stories": stories}

        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}

        finally:
            if conn:
                conn.close()

    def delete_expired_stories(self):
        """
    Deletes stories older than 24 hours from both the database and disk.

    Behavior:
        - Calculates a cutoff datetime (24 hours ago).
        - Selects expired media entries from the database.
        - Removes their associated files from the filesystem.
        - Deletes matching DB records.
        - Returns a status JSON response with the number of deleted stories.

    Returns:
        dict: {
            "status": "success" or "error",
            "message": description string
        }
    """
        cutoff = (
                datetime.now() -
                timedelta(hours=HOURS_IN_A_DAY)
        ).strftime("%Y-%m-%d %H:%M:%S")

        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Select expired media
            cursor.execute("""
                SELECT content FROM stories
                WHERE timestamp <= ? AND content_type IN ('image', 'video')
            """, (cutoff,))
            expired_media = cursor.fetchall()

            # Delete files
            for (filename,) in expired_media:
                file_path = os.path.join(STORIES_FOLDER, filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass

            # Delete DB rows
            cursor.execute(
                "DELETE FROM stories WHERE timestamp <= ?",
                (cutoff,)
            )
            deleted_count = cursor.rowcount
            conn.commit()

            return (
                {"status": "success",
                 "message": f"Deleted {deleted_count} expired stories."}
            )

        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}

        finally:
            if conn:
                conn.close()

    def handle_request(self, request_type, payload):
        """
            Dispatches a request from the client to the matching handler.

            Supported requests:
                - "ADD_STORY": Saves a new story.
                - "GET_STORIES": Returns a combined view
                 of stories from DB and folder.
                - "DELETE_EXPIRED_STORIES": Removes old stories (>24h)."""

        if request_type == "ADD_STORY":
            return self.add_story(payload)
        if request_type == "GET_STORIES":
            return self.get_stories_from_folder()
        if request_type == "DELETE_EXPIRED_STORIES":
            return self.delete_expired_stories()

        return {"status": "error", "message": "Unknown request type."}

    def get_stories_from_folder(self):
        """
        Returns a combined list of story metadata from both the filesystem
    and the database.

    Behavior:
        1. Ensures the STORIES folder exists.
        2. Collects the list of media files from the filesystem.
        3. Loads recent (≤24 hours) story records from the database.
        4. Matches DB entries with actual existing media files.
        5. Adds media files that exist in the folder but do NOT appear in DB.
           (User might have manually added a file)
        6. Normalizes and infers metadata:
            - filename
            - username (derived from filename if needed)
            - content_type ("photo" or "video")
            - timestamp
        7. Sorts results newest → oldest.
        """
        try:
            if not os.path.exists(STORY_FOLDER):
                os.makedirs(STORY_FOLDER)

            files_in_folder = set(os.listdir(STORY_FOLDER))
            valid_extensions = [
                '.jpg', '.jpeg', '.png',
                '.bmp', '.mp4', '.avi',
                '.mov'
            ]
            media_files = {
                f
                for f in files_in_folder
                if os.path.splitext(f)[FILE_EXTENSION_INDEX].lower()
                in valid_extensions
            }

            stories = []

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cutoff = (
                    datetime.now() -
                    timedelta(hours=HOURS_IN_A_DAY)
            ).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                SELECT username, content_type, filename, timestamp
                FROM stories
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (cutoff,))

            db_stories = cursor.fetchall()
            conn.close()

            for username, content_type, filename, timestamp in db_stories:
                if filename in media_files:
                    stories.append({
                        'filename': filename,
                        'username': username,
                        'timestamp': timestamp,
                        'content_type': content_type
                    })

            for filename in media_files:
                if not any(s['filename'] == filename for s in stories):
                    file_path = os.path.join(STORY_FOLDER, filename)
                    file_stat = os.stat(file_path)
                    timestamp = (
                        datetime.fromtimestamp(file_stat.st_mtime)
                        .strftime('%Y-%m-%d %H:%M:%S')
                    )

                    username_parts = filename.split('_')
                    username = (
                        username_parts[FIRST_PART_INDEX]
                        if len(username_parts) > MIN_PARTS_WITH_SEPARATOR
                        else "Unknown"
                    )

                    ext = Path(filename).suffix.lower()
                    content_type = (
                        "video"
                        if ext in ['.mp4', '.avi', '.mov']
                        else "photo"
                    )

                    stories.append({
                        'filename': filename,
                        'username': username,
                        'timestamp': timestamp,
                        'content_type': content_type
                    })

            stories.sort(key=lambda x: x['timestamp'], reverse=True)

            print(f"[DEBUG] Found {len(stories)} stories in folder")

            return {"status": "success", "stories": stories}

        except Exception as e:
            print(f"[ERROR] get_stories_from_folder: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e), "stories": []}
