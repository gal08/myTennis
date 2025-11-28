import sqlite3
import time
import os
import base64
from datetime import datetime, timedelta

import story_saver_server
from Protocol import Protocol

# DB configuration
DB_NAME = 'users.db'
STORIES_FOLDER = "stories"


class StoriesHandler:
    """
    Handles ADD_STORY and GET_STORIES operations with support for text, images, and videos.
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
        """Ensures the 'stories' table exists with support for different content types."""
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
                    content_type TEXT NOT NULL DEFAULT 'text' CHECK(content_type IN ('text', 'image', 'video')),
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
                print("ERROR: stories table missing content_type column. Please migrate manually.")

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
                'content_type': 'text'|'image'|'video',
                'content': base64 or text,
                'filename': '' (ignored for media)
            }
        """
        username = payload.get('username')
        filename = payload.get('file_name')
        return {
            "status": "success",
            "message": "story posted successfully!"
        }

        """timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        if not all([username, content]):
            return {
                "status": "error",
                "message": "Missing required fields (username or content)."
            }

        if content_type not in ['text', 'image', 'video']:
            return {
                "status": "error",
                "message": "Invalid content type. Must be 'text', 'image', or 'video'."
            }

        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Handle media: save as file, store only filename in DB
            stored_filename = None

            if content_type in ['image', 'video']:
                # Generate unique filename
                ext = ".jpg" if content_type == "image" else ".mp4"
                stored_filename = f"{username}_{int(time.time())}{ext}"
                file_path = os.path.join(STORIES_FOLDER, stored_filename)

                try:
                    file_bytes = base64.b64decode(content)
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Failed to decode base64: {e}"
                    }

                try:
                    with open(file_path, "wb") as f:
                        f.write(file_bytes)
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Failed to write media file: {e}"
                    }

                stored_content = stored_filename

            else:
                # Text story only
                stored_content = content

            cursor.execute(
                "INSERT INTO stories (username, content_type, content, filename, timestamp) VALUES (?, ?, ?, ?, ?)",
                (username, content_type, stored_content, stored_filename, timestamp)
            )
            conn.commit()

            return {
                "status": "success",
                "message": f"{content_type.capitalize()} story posted successfully!"
            }

        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}

        finally:
            if conn:
                conn.close()"""

    def get_stories(self, payload):
        """
        Retrieves all stories from the last 24 hours.
        Returns file paths for image/video stories.
        """
        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

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
        cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

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
            cursor.execute("DELETE FROM stories WHERE timestamp <= ?", (cutoff,))
            deleted_count = cursor.rowcount
            conn.commit()

            return {"status": "success", "message": f"Deleted {deleted_count} expired stories."}

        except Exception as e:
            return {"status": "error", "message": f"Database error: {e}"}

        finally:
            if conn:
                conn.close()

    def handle_request(self, request_type, payload):
        if request_type == "ADD_STORY":
            return self.add_story(payload)
        if request_type == "GET_STORIES":
            return self.get_stories(payload)
        if request_type == "DELETE_EXPIRED_STORIES":
            return self.delete_expired_stories()

        return {"status": "error", "message": "Unknown request type."}