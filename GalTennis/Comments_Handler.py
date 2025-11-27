import sqlite3  # Imports the SQLite library
import time     # Imports the time module

# DB configuration - Standardized name
DB_NAME = 'users.db'  # Defines the file name for the SQLite database.

COMMENT_USERNAME_INDEX = 0
COMMENT_CONTENT_INDEX = 1
COMMENT_TIMESTAMP_INDEX = 2


class CommentsHandler:
    """
    Handles ADD_COMMENT and GET_COMMENTS operations against the 'comments' database table.
    """

    def __init__(self):  # Class constructor.
        # We use the global DB_NAME defined above
        self._initialize_db()    # Calls the method to ensure the necessary table exists.

    @staticmethod
    def _initialize_db():    # Method to set up the database table.
        """Ensures the 'comments' table exists, storing details about video comments."""
        conn = sqlite3.connect(DB_NAME)  # Establishes a connection to the database.
        cursor = conn.cursor()          # Creates a cursor object to execute SQL commands.
        cursor.execute("""               # Executes SQL to create the 'comments' table if it doesn't exist.
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, # Unique identifier for each comment.
                video_filename TEXT NOT NULL,  # The filename of the video the comment is attached to.
                username TEXT NOT NULL,        # The user who posted the comment.
                content TEXT NOT NULL,         # The text content of the comment.
                timestamp TEXT NOT NULL        # The time the comment was posted.
                -- Foreign key checks omitted for SQLite simplicity
            )
        """)
        conn.commit()  # Saves the transaction/changes to the database file.
        conn.close()   # Closes the database connection.

    @staticmethod
    def add_comment(payload):      # Method to insert a new comment into the DB.
        """
        Adds a new comment to the database.
        Expected payload: {'username': 'user1', 'video_title': 'video_1.mp4', 'content': 'Great shot!'}
        """
        username = payload.get('username')  # Extracts the username from the request payload.
        # Client sends 'video_title', which maps to 'video_filename' in DB
        video_filename = payload.get('video_title')  # Extracts the video title (used as filename).
        content = payload.get('content')       # Extracts the comment text content.

        # Using a readable timestamp for the client
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")  # Generates the current timestamp in string format.

        if not all([username, video_filename, content]):  # Checks if all required fields are present.
            # Returns an error if fields are missing.
            return {"status": "error", "message": "Missing required fields for comment."}

        conn = None                          # Initializes the connection variable to None.
        try:                                 # Start of error handling block for database operations.
            conn = sqlite3.connect(DB_NAME)  # Connects to the database.
            cursor = conn.cursor()           # Creates a cursor.
            # Executes SQL to insert the new comment.
            cursor.execute("INSERT INTO comments (video_filename, username, content, timestamp) VALUES (?, ?, ?, ?)",
                           (video_filename, username, content, timestamp))  # Binds the values to the placeholders.
            conn.commit()                    # Commits the changes.
            return {"status": "success", "message": "Comment added successfully."}  # Returns a success message.

        except sqlite3.Error as e:           # Catches specific SQLite errors.
            return {"status": "error", "message": f"Database error: {e}"}  # Returns a database error message.
        finally:                             # Runs regardless of success or failure.
            if conn:                         # Checks if the connection object exists.
                conn.close()                 # Closes the database connection.

    @staticmethod
    def get_comments(payload):     # Method to retrieve comments for a video.
        """
        Retrieves all comments for a specific video, ordered by time.
        Expected payload: {'video_title': 'video_1.mp4'}
        """
        # Client sends 'video_title', which maps to 'video_filename' in DB
        video_filename = payload.get('video_title')  # Extracts the video title (filename).

        if not video_filename:               # Checks if the video title is provided.
            return {"status": "error", "message": "Missing video title."}  # Returns an error if missing.

        conn = None                          # Initializes the connection variable.
        try:                                 # Start of error handling block.
            conn = sqlite3.connect(DB_NAME)  # Connects to the database.
            cursor = conn.cursor()           # Creates a cursor.

            # Select comments and order them ascending by time
            cursor.execute(                  # Executes SQL to select comments for the video, ordered by timestamp.
                "SELECT username, content, timestamp FROM comments WHERE video_filename=? ORDER BY timestamp ASC",
                (video_filename,))           # Binds the video filename.
            comments_data = cursor.fetchall()  # Fetches all matching comment rows.
            # Converts the list of tuples into a list of dictionaries (for JSON output)
            comments = []
            for row in comments_data:
                comments.append({
                    "username": row[COMMENT_USERNAME_INDEX],
                    "content": row[COMMENT_CONTENT_INDEX],
                    "timestamp": row[COMMENT_TIMESTAMP_INDEX]
                })

            return {"status": "success", "comments": comments}  # Returns success with the list of comments.

        except sqlite3.Error as e:           # Catches specific SQLite errors.
            return {"status": "error", "message": f"Database error: {e}"}  # Returns a database error message.
        finally:                             # Runs regardless of success or failure.
            if conn:                         # Checks if the connection object exists.
                conn.close()                 # Closes the database connection.

    def handle_request(self, request_type, payload):  # Method to route incoming requests.
        """Routes the comment request to the appropriate method based on request_type."""
        if request_type == 'ADD_COMMENT':    # Checks if the request is to add a comment.
            return self.add_comment(payload)  # Calls the add_comment method.
        elif request_type == 'GET_COMMENTS':  # Checks if the request is to retrieve comments.
            return self.get_comments(payload)  # Calls the get_comments method.
        else:
            # Returns an error for an unknown request type.
            return {"status": "error", "message": "Unknown comment request type."}
