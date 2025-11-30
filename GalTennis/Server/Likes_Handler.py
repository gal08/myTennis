"""
Gal Haham
Video like/unlike system handler.
Manages like toggles and like count retrieval with
database persistence.
"""
import sqlite3
import time

DB_NAME = 'users.db'
SINGLE_RESULT_COLUMN_INDEX = 0


class LikesHandler:
    """
    Handles LIKE and UNLIKE operations against the 'likes' database table.
    """

    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Ensures the 'likes' table exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # It was only used for schema correction. We will align the schema now.

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                video_filename TEXT NOT NULL,
                username TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (video_filename) REFERENCES videos(title),
                UNIQUE (video_filename, username)
            )
        """)
        conn.commit()
        conn.close()

    def get_likes_count(self, payload):
        """
        Retrieves the total number of likes for a given video.
        Expected payload: {'title': 'forehand_easy_1.mp4'}
        """
        video_title_key = payload.get('video_title') or payload.get('title')

        if not video_title_key:
            return {
                "status": "error",
                "message": "Missing video title for likes count."
            }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Note: We now query by the correct column name 'video_filename'
            cursor.execute(
                "SELECT COUNT(*) FROM likes WHERE video_filename=?",
                (video_title_key,)
            )

            count = cursor.fetchone()[SINGLE_RESULT_COLUMN_INDEX]
            conn.close()
            return {"status": "success", "count": count}

        except sqlite3.Error as e:
            return {"status": "error", "message": f"Database error: {e}"}
        except Exception as e:
            return {
                "status": "error",
                "message": f"An unexpected error occurred: {e}"
            }

    def handle_like_toggle(self, payload):
        """
        Handles the LIKE_VIDEO request (toggles between Like and Unlike).
        Expected payload from Client: {'username': 'user1',
        'title': 'forehand_easy_1.mp4'}
        """
        username = payload.get('username')
        # Client sends 'title', which corresponds to video_filename in the DB
        video_filename = payload.get('title')

        if not all([username, video_filename]):
            return {
                "status": "error",
                "message": (
                    "Username and Video Title are required "
                    "to like a video."
                )
            }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            """Check if the user already liked the video
             (using the correct DB column name)"""
            cursor.execute(
                "SELECT 1 FROM likes "
                "WHERE username=? AND video_filename=?",
                (username, video_filename)
            )

            existing_like = cursor.fetchone()

            if existing_like:
                # If like exists, remove it (Unlike)
                cursor.execute(
                    "DELETE FROM likes "
                    "WHERE username=? AND video_filename=?",
                    (username, video_filename)
                )

                conn.commit()
                message = "Like removed (Unlike)."
            else:
                # If like does not exist, add it
                cursor.execute(
                    "INSERT INTO likes (username, video_filename) "
                    "VALUES (?, ?)",
                    (username, video_filename)
                )

                conn.commit()
                message = "Video liked successfully."

            conn.close()
            # Return is_liked status for client to update UI
            return {
                "status": "success",
                "message": message,
                "is_liked": not existing_like
            }

        except sqlite3.Error as e:
            return {"status": "error", "message": f"Database error: {e}"}
        except Exception as e:
            return {
                "status": "error",
                "message": f"An unexpected error occurred: {e}"
            }

    def handle_request(self, request_type, payload):
        """Routes the like request to the appropriate
         method based on request_type."""
        if request_type == 'LIKE_VIDEO':
            return self.handle_like_toggle(payload)
        elif request_type == 'GET_LIKES_COUNT':
            # This is called by the client when viewing the video list
            return self.get_likes_count(payload)
        else:
            return {"status": "error", "message": "Unknown like request type."}
