"""
Gal Haham
Video like/unlike system handler.
Manages like toggles and like count retrieval with database persistence.
NOW USES DBManager for all database operations.
"""
from Db_manager import get_db_manager


class LikesHandler:
    """
    Handles LIKE and UNLIKE operations using DBManager.
    """

    def __init__(self):
        """Initialize with DBManager."""
        self.db = get_db_manager()

    def get_likes_count(self, payload):
        """
        Retrieves the total number of likes for a given video.
        Expected payload: {'title': 'forehand_easy_1.mp4'}
         or {'video_title': '...'}
        """
        video_title = payload.get('video_title') or payload.get('title')

        if not video_title:
            return {
                "status": "error",
                "message": "Missing video title for likes count."
            }

        # Use DBManager to get likes count
        count = self.db.get_likes_count(video_title)
        return {"status": "success", "count": count}

    def handle_like_toggle(self, payload):
        """
        Handles the LIKE_VIDEO request (toggles between Like and Unlike).
        Expected payload: {'username': 'user1', 'title': 'forehand_easy_1.mp4'}
        """
        username = payload.get('username')
        video_filename = payload.get('title')  # Client sends 'title'

        if not all([username, video_filename]):
            return {
                "status": "error",
                "message": (
                    "Username and Video Title are required "
                    "to like a video."
                ),
            }
        # Use DBManager to toggle like
        return self.db.toggle_like(video_filename, username)

    def handle_request(self, request_type, payload):
        """Routes the like request to the appropriate method."""
        if request_type == 'LIKE_VIDEO':
            return self.handle_like_toggle(payload)
        elif request_type == 'GET_LIKES_COUNT':
            return self.get_likes_count(payload)
        else:
            return {"status": "error", "message": "Unknown like request type."}