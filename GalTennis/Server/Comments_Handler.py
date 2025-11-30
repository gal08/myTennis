"""
Gal Haham
Video comment system handler.
Manages adding and retrieving comments for videos with timestamp tracking.
"""
import sqlite3
import time  # time is needed for generating the timestamp

# DB configuration - Standardized name
DB_NAME = 'users.db'
USERNAME_INDEX = 0
CONTENT_INDEX = 1
TIMESTAMP_INDEX = 2


class CommentsHandler:
    """
    Handles ADD_COMMENT and GET_COMMENTS operations
    against the 'comments' database table.
    """

    def __init__(self):
        # We use the global DB_NAME defined above
        self._initialize_db()

    def _initialize_db(self):
        """
        Ensures the 'comments' table exists,
        storing details about video comments.
        """
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        create_table_sql = (
            "CREATE TABLE IF NOT EXISTS comments ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "video_filename TEXT NOT NULL, "
            "username TEXT NOT NULL, "
            "content TEXT NOT NULL, "
            "timestamp TEXT NOT NULL"
            ")"
        )

        cursor.execute(create_table_sql)
        conn.commit()
        conn.close()

    def add_comment(self, payload):
        """
        Adds a new comment to the database.
        Expected payload: {'username': 'user1', 'video_title':
         'video_1.mp4', 'content': 'Great shot!'}
        """
        username = payload.get('username')
        # Client sends 'video_title', which maps to 'video_filename' in DB
        video_filename = payload.get('video_title')
        content = payload.get('content')

        # Using a readable timestamp for the client
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        if not all([username, video_filename, content]):
            return {
                "status": "error",
                "message": "Missing required fields for comment."
            }

        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO comments "
                "(video_filename, username, content, timestamp) "
                "VALUES (?, ?, ?, ?)",
                (
                    video_filename,
                    username,
                    content,
                    timestamp
                )
            )

            conn.commit()
            return {
                "status": "success",
                "message": "Comment added successfully."
            }

        except sqlite3.Error as e:
            return {"status": "error", "message": f"Database error: {e}"}
        finally:
            if conn:
                conn.close()

    def get_comments(self, payload):
        """
        Retrieves all comments for a specific video, ordered by time.
        Expected payload: {'video_title': 'video_1.mp4'}
        """
        # Client sends 'video_title', which maps to 'video_filename' in DB
        video_filename = payload.get('video_title')

        if not video_filename:
            return {"status": "error", "message": "Missing video title."}

        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Select comments and order them ascending by time
            cursor.execute(
                (
                    "SELECT username, content, timestamp "
                    "FROM comments "
                    "WHERE video_filename=? "
                    "ORDER BY timestamp ASC"
                ),
                (video_filename,)
            )

            comments_data = cursor.fetchall()

            comments = [
                {
                    "username": row[USERNAME_INDEX],
                    "content": row[CONTENT_INDEX],
                    "timestamp": row[TIMESTAMP_INDEX]
                }
                for row in comments_data
            ]

            return {"status": "success", "comments": comments}

        except sqlite3.Error as e:
            return {"status": "error", "message": f"Database error: {e}"}
        finally:
            if conn:
                conn.close()

    def handle_request(self, request_type, payload):
        """Routes the comment request to the
        appropriate method based on request_type."""
        if request_type == 'ADD_COMMENT':
            return self.add_comment(payload)
        elif request_type == 'GET_COMMENTS':
            return self.get_comments(payload)
        else:
            return {
                "status": "error",
                "message": "Unknown comment request type."
            }
