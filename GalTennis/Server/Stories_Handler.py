import sqlite3
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

STORIES_FOLDER = "stories"

STORY_FOLDER = "stories"


# DB configuration
DB_NAME = 'users.db'


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
            columns = [column[1] for column in cursor.fetchall()]

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
        ext = os.path.splitext(filename)[1]
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
                timedelta(hours=24)
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
                    "username": row[0],
                    "content_type": row[1],
                    "content": row[2],
                    "filename": row[3],
                    "timestamp": row[4],
                    "id": row[5],
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
        Deletes stories older than 24 hours and their media files.
        """
        cutoff = (
                datetime.now() -
                timedelta(hours=24)
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
        if request_type == "ADD_STORY":
            return self.add_story(payload)
        if request_type == "GET_STORIES":
            return self.get_stories_from_folder()
        if request_type == "DELETE_EXPIRED_STORIES":
            return self.delete_expired_stories()

        return {"status": "error", "message": "Unknown request type."}

    def get_stories_from_folder(self):
        """
        Returns all stories from folder AND database (combined view)
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
                if os.path.splitext(f)[1].lower() in valid_extensions
            }

            stories = []

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cutoff = (
                    datetime.now() -
                    timedelta(hours=24)
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
                        username_parts[0]
                        if len(username_parts) > 1
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
