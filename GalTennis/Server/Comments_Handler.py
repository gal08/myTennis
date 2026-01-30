"""
Gal Haham
Video comment system handler.
Manages adding and retrieving comments for videos with timestamp tracking.
NOW USES DBManager for all database operations.
"""
import time
from Db_manager import get_db_manager


class CommentsHandler:
    """
    Handles ADD_COMMENT and GET_COMMENTS operations using DBManager.
    """

    def __init__(self):
        """Initialize with DBManager."""
        self.db = get_db_manager()

    def add_comment(self, payload):
        """
        Adds a new comment to the database using DBManager.
        Expected payload: {'username': 'user1', 'video_title':
        'video_1.mp4', 'content': 'Great shot!'}
        """
        username = payload.get('username')
        video_filename = payload.get('video_title')
        # Client sends 'video_title'
        content = payload.get('content')

        if not all([username, video_filename, content]):
            return {
                "status": "error",
                "message": "Missing required fields for comment."
            }

        # Generate readable timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Use DBManager to add comment
        return self.db.add_comment(
            video_filename,
            username,
            content,
            timestamp,
        )

    def get_comments(self, payload):
        """
        Retrieves all comments for a specific video using DBManager.
        Expected payload: {'video_title': 'video_1.mp4'}
        """
        video_filename = payload.get('video_title')
        # Client sends 'video_title'

        if not video_filename:
            return {"status": "error", "message": "Missing video title."}

        # Use DBManager to get comments
        comments = self.db.get_comments(video_filename)
        return {"status": "success", "comments": comments}

    def handle_request(self, request_type, payload):
        """Routes the comment request to the appropriate method."""
        if request_type == 'ADD_COMMENT':
            return self.add_comment(payload)
        elif request_type == 'GET_COMMENTS':
            return self.get_comments(payload)
        else:
            return {
                "status": "error",
                "message": "Unknown comment request type."
            }