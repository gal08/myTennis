"""
Gal Haham
Video metadata management system.
Handles video upload registration and retrieval
with category/difficulty validation.
NOW USES DBManager for all database operations.
"""
import time
from Db_manager import get_db_manager

ALLOWED_CATEGORIES = (
    'forehand', 'backhand', 'serve',
    'slice', 'volley', 'smash'
)
ALLOWED_DIFFICULTIES = ('easy', 'medium', 'hard')


class VideosHandler:
    """
    Class for managing video content: adding and retrieving the video list.
    Handles 'ADD_VIDEO' and 'GET_VIDEOS' requests.
    NOW USES DBManager for database operations.
    """

    def __init__(self):
        """Initialize with DBManager. Schema is created automatically."""
        self.db = get_db_manager()

    def add_video(self, payload):
        """
        Adds a new video record to the DB using DBManager.
        """
        title = payload.get("title")
        category = payload.get("category")
        level = payload.get("level")
        uploader = payload.get("uploader")

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

        # Use DBManager to add video
        current_time = time.time()
        return self.db.add_video(
            title,
            uploader,
            category,
            level,
            current_time
        )

    def get_videos(self):
        """
        Retrieves all available videos using DBManager,
        ordered by latest upload (timestamp).
        """
        videos = self.db.get_all_videos()
        return {"status": "success", "videos": videos}

    def handle_request(self, request_type, payload):
        """Routes video requests to appropriate methods."""
        if request_type == 'ADD_VIDEO':
            return self.add_video(payload)
        elif request_type == 'GET_VIDEOS':
            return self.get_videos()

        return {"status": "error", "message": "Unknown video request"}