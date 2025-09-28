import sqlite3
import time
from datetime import datetime, timedelta

# DB configuration - Standardized name
DB_NAME = 'users.db'


class StoriesHandler:
    """
    Handles ADD_STORY and GET_STORIES operations against the 'stories' database table.
    Includes logic for 24-hour expiration based on the timestamp.
    """

    def __init__(self):
        # We use the global DB_NAME defined above
        self._initialize_db()

    def _initialize_db(self):
        """Ensures the 'stories' table exists."""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                content TEXT NOT NULL, 
                timestamp TEXT NOT NULL
                -- Foreign key checks omitted for SQLite simplicity
            )
        """)
        conn.commit()
        conn.close()

    def add_story(self, payload):
        """
        Adds a new story to the database.
        Expected payload: {'username': 'user1', 'content': 'Just finished practice!'}
        """
        username = payload.get('username')
        content = payload.get('content')

        # Using a readable timestamp for accurate SQLite comparison with datetime
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        if not all([username, content]):
            return {"status": "error", "message": "Missing required fields for story (username or content)."}

        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO stories (username, content, timestamp) VALUES (?, ?, ?)",
                           (username, content, timestamp))
            conn.commit()
            return {"status": "success", "message": "Story posted successfully. It will expire in 24 hours."}

        except sqlite3.Error as e:
            return {"status": "error", "message": f"Database error: {e}"}
        finally:
            if conn:
                conn.close()

    def get_stories(self, payload):
        """
        Retrieves all stories posted within the last 24 hours.
        Old stories are automatically excluded by the query.
        """
        # Calculate the timestamp 24 hours ago in the correct format for SQLite comparison
        # This allows SQLite to perform the date/time comparison efficiently
        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Retrieve only stories where the timestamp is greater (more recent) than 24 hours ago
            cursor.execute("""
                SELECT username, content, timestamp 
                FROM stories 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
                """,
                           (twenty_four_hours_ago,))
            stories_data = cursor.fetchall()

            stories = [{"username": row[0], "content": row[1], "timestamp": row[2]} for row in stories_data]

            return {"status": "success", "stories": stories}

        except sqlite3.Error as e:
            return {"status": "error", "message": f"Database error: {e}"}
        finally:
            if conn:
                conn.close()

    def handle_request(self, request_type, payload):
        """Routes the story request to the appropriate method."""
        if request_type == 'ADD_STORY':
            return self.add_story(payload)
        elif request_type == 'GET_STORIES':
            return self.get_stories(payload)
        else:
            return {"status": "error", "message": "Unknown story request type."}
