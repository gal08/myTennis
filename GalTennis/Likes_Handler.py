import sqlite3               # Imports the SQLite library

DB_NAME = 'users.db'         # Defines the file name for the SQLite database.

SINGLE_RESULT_INDEX = 0


class LikesHandler:          # Defines the handler class for video like/unlike operations.
    """
    Handles LIKE and UNLIKE operations against the 'likes' database table.
    """

    def __init__(self, db_path=DB_NAME):  # Class constructor, optionally accepts a custom database path.
        self.db_path = db_path           # Stores the database path as an instance variable.
        self._initialize_db()            # Calls the method to ensure the 'likes' table exists.

    def _initialize_db(self):    # Method to set up the 'likes' database table.
        """Ensures the 'likes' table exists."""
        conn = sqlite3.connect(self.db_path)  # Connects to the SQLite database.
        cursor = conn.cursor()               # Creates a cursor object.

        # --- REMOVING DROP TABLE: We must remove the DROP TABLE to prevent data loss on every run.
        # It was only used for schema correction. We will align the schema now.

        cursor.execute("""                   # Executes SQL to create the 'likes' table if it doesn't exist.
            CREATE TABLE IF NOT EXISTS likes (
                video_filename TEXT NOT NULL,  # The filename of the video that was liked.
                username TEXT NOT NULL,        # The user who performed the like action.
                FOREIGN KEY:
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (video_filename) REFERENCES videos(title),
                
                UNIQUE (video_filename, username)
            )
        """)
        conn.commit()                      # Saves the transaction/changes.
        conn.close()                       # Closes the database connection.

    def get_likes_count(self, payload):  # Method to fetch the total number of likes for a video.
        """
        Retrieves the total number of likes for a given video.
        Expected payload: {'title': 'forehand_easy_1.mp4'}
        """
        # The client sends 'title', which corresponds to video_filename in the DB
        # Extracts the video title/filename from the payload.
        video_title_key = payload.get('video_title') or payload.get('title')

        if not video_title_key:          # Checks if the required video title is missing.
            # Returns an error if missing.
            return {"status": "error", "message": "Missing video title for likes count."}

        try:                             # Start of error handling block.
            conn = sqlite3.connect(self.db_path)  # Connects to the database.
            cursor = conn.cursor()       # Creates a cursor.
            # Queries the number of likes for the specified video.
            cursor.execute("SELECT COUNT(*) FROM likes WHERE video_filename=?", (video_title_key,))
            count = cursor.fetchone()[SINGLE_RESULT_INDEX]  # Fetches the single count result
            conn.close()                 # Closes the database connection.
            return {"status": "success", "count": count}  # Returns the successful count result.

        except sqlite3.Error as e:       # Catches specific SQLite errors.
            # Returns a database error message.
            return {"status": "error", "message": f"Database error: {e}"}
        except Exception as e:           # Catches any unexpected general errors.
            # Returns a general error message.
            return {"status": "error", "message": f"An unexpected error occurred: {e}"}

    def handle_like_toggle(self, payload):  # Method to handle the like/unlike action.
        """
        Handles the LIKE_VIDEO request (toggles between Like and Unlike).
        Expected payload from Client: {'username': 'user1', 'title': 'forehand_easy_1.mp4'}
        """
        username = payload.get('username')   # Extracts the username.
        # Client sends 'title', which corresponds to video_filename in the DB
        video_filename = payload.get('title')  # Extracts the video filename.

        if not all([username, video_filename]):  # Checks if both required fields are present.
            # Returns error if fields are missing.
            return {"status": "error", "message": "Username and Video Title are required to like a video."}

        try:                                 # Start of error handling block.
            conn = sqlite3.connect(self.db_path)  # Connects to the database.
            cursor = conn.cursor()           # Creates a cursor.

            # Check if the user already liked the video (using the correct DB column name)
            # Checks for an existing like record.
            cursor.execute("SELECT 1 FROM likes WHERE username=? AND video_filename=?", (username, video_filename))
            existing_like = cursor.fetchone()  # Fetches the result (None if no like exists, tuple if it does).

            if existing_like:                # Condition: If a like record was found (user already liked it).
                # If like exists, remove it (Unlike)
                # Deletes the existing like record.
                cursor.execute("DELETE FROM likes WHERE username=? AND video_filename=?", (username, video_filename))
                conn.commit()                # Commits the deletion.
                message = "Like removed (Unlike)."  # Sets the message for "Unlike."
            else:   # Condition: If no like record was found (user has not liked it yet).
                # If like does not exist, add it
                # Inserts a new like record.
                cursor.execute("INSERT INTO likes (username, video_filename) VALUES (?, ?)", (username, video_filename))
                conn.commit()                # Commits the insertion.
                message = "Video liked successfully."  # Sets the message for "Like."

            conn.close()                     # Closes the database connection.
            # Return is_liked status for client to update UI
            # Returns success along with the new like status.
            return {"status": "success", "message": message, "is_liked": not existing_like}

        except sqlite3.Error as e:           # Catches specific SQLite errors.
            # Returns a database error message.
            return {"status": "error", "message": f"Database error: {e}"}
        except Exception as e:               # Catches any unexpected general errors.
            # Returns a general error message.
            return {"status": "error", "message": f"An unexpected error occurred: {e}"}

    def handle_request(self, request_type, payload):  # Method to route incoming requests.
        """Routes the like request to the appropriate method based on request_type."""
        if request_type == 'LIKE_VIDEO':  # Checks if the request is to toggle the like status.
            return self.handle_like_toggle(payload)  # Calls the like/unlike handler.
        elif request_type == 'GET_LIKES_COUNT':  # Checks if the request is to get the like count.
            # This is called by the client when viewing the video list
            return self.get_likes_count(payload)  # Calls the count retrieval method.
        else:  # Returns an error for an unrecognized request.
            return {"status": "error", "message": "Unknown like request type."}
