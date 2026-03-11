"""
Gal Haham
Video metadata management system.
Handles video upload registration and retrieval
with category/difficulty validation.
NOW USES DBManager for all database operations.
"""
import time
import os
import base64
from Db_manager import get_db_manager

ALLOWED_CATEGORIES = (
    'forehand', 'backhand', 'serve',
    'slice', 'volley', 'smash'
)
ALLOWED_DIFFICULTIES = ('easy', 'medium', 'hard')


class VideosHandler:
    def __init__(self):
        self.db = get_db_manager()
        self.videos_folder = self._ensure_videos_folder()

    def _ensure_videos_folder(self):
        """
        Ensure videos folder exists and return its path.

        Returns:
            str: Path to videos folder
        """
        # Get server directory (where this file is located)
        server_dir = os.path.dirname(os.path.abspath(__file__))
        videos_folder = os.path.join(server_dir, "videos")

        # Create folder if doesn't exist
        if not os.path.exists(videos_folder):
            os.makedirs(videos_folder)
            print(f"[DEBUG] Created videos folder: {videos_folder}")

        return videos_folder

    def upload_video(self, payload):
        """
        Handle video upload - receive file over network and save it.

        Args:
            payload: Dict containing title, category,
            level, uploader, file_content

        Returns:
            dict: Response with status and message
        """
        try:
            # Extract data
            title = payload.get("title")
            category = payload.get("category")
            level = payload.get("level")
            uploader = payload.get("uploader")
            file_content_b64 = payload.get("file_content")

            # Validate required fields
            if not all([title, category, level, uploader, file_content_b64]):
                return {
                    "status": "error",
                    "message": (
                        "Missing required fields "
                        "(title, category, level, uploader, or file_content)."
                    )
                }
            # Validate category and level
            if (
                    category not in ALLOWED_CATEGORIES or
                    level not in ALLOWED_DIFFICULTIES
            ):
                return {
                    "status": "error",
                    "message": "Invalid category or difficulty level."
                }

            # Decode and save file
            file_path = os.path.join(self.videos_folder, title)

            # Check if file already exists on disk
            if os.path.exists(file_path):
                return {
                    "status": "error",
                    "message": (
                        f"A file named '{title}' already exists "
                        "in videos folder."
                    )
                }
            try:
                # Decode base64 and write file
                file_data = base64.b64decode(file_content_b64)
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                print(f"[DEBUG] Video file saved: {file_path}")

            except Exception as file_err:
                print(f"[DEBUG] Error saving file: {file_err}")
                return {
                    "status": "error",
                    "message": f"Failed to save video file: {str(file_err)}"
                }

            # Add to database
            current_time = time.time()
            db_response = self.db.add_video(
                title,
                uploader,
                category,
                level,
                current_time
            )

            # If database insert failed, delete the file
            if db_response.get("status") != "success":
                try:
                    os.remove(file_path)
                    print(f"Deleted file after DB failure: {file_path}")
                except Exception as del_err:
                    print(f"Could not delete file: {del_err}")

                return db_response

            print(f"[DEBUG] Video uploaded successfully: {title}")
            return {
                "status": "success",
                "message": f"Video '{title}' uploaded successfully!"
            }

        except Exception as e:
            print(f"[DEBUG] Upload error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error uploading video: {str(e)}"
            }

    def add_video(self, payload):
        """
        Legacy method - add video metadata only (no file upload).
        Kept for backward compatibility.

        Args:
            payload: Dict containing title, category, level, uploader

        Returns:
            dict: Response with status and message
        """
        try:
            title = payload.get("title")
            category = payload.get("category")
            level = payload.get("level")
            uploader = payload.get("uploader")

            if not all([title, category, level, uploader]):
                return {
                    "status": "error",
                    "message": (
                        "Missing video title, category, level, "
                        "or uploader in request."
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

            current_time = time.time()
            return self.db.add_video(
                title,
                uploader,
                category,
                level,
                current_time
            )
        except Exception as e:
            print(f"[DEBUG] Error in add_video: {e}")
            return {
                "status": "error",
                "message": "Error adding video"
            }

    def get_videos(self):
        """
        Get all videos from database.

        Returns:
            dict: Response with status and videos list
        """
        try:
            videos = self.db.get_all_videos()
            return {"status": "success", "videos": videos}
        except:
            return {
                "status": "error",
                "message": "Error retrieving videos"
            }

    def handle_request(self, request_type, payload):
        """
        Route video-related requests to appropriate handlers.

        Args:
            request_type: Type of request (UPLOAD_VIDEO, ADD_VIDEO, GET_VIDEOS)
            payload: Request data

        Returns:
            dict: Response from handler
        """
        try:
            if request_type == 'UPLOAD_VIDEO':
                return self.upload_video(payload)
            elif request_type == 'ADD_VIDEO':
                return self.add_video(payload)
            elif request_type == 'GET_VIDEOS':
                return self.get_videos()

            return {"status": "error", "message": "Unknown video request"}
        except:
            return {
                "status": "error",
                "message": "Error handling video request"
            }
