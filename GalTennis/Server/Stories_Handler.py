"""
Gal Haham
Story management system with 24-hour expiration.
Handles story creation, retrieval, and automatic cleanup of expired content.
NOW USES DBManager for all database operations.
✅ FIXED: Auto-cleanup of expired stories on every GET_STORIES request.
"""
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from Db_manager import get_db_manager

STORIES_FOLDER = "stories"
STORY_FOLDER = "stories"
HOURS_IN_A_DAY = 24
FILE_EXTENSION_INDEX = 1
FIRST_PART_INDEX = 0
MIN_PARTS_WITH_SEPARATOR = 1


class StoriesHandler:
    """
    Handles ADD_STORY and GET_STORIES operations with DBManager.
    Stories expire after 24 hours.
    ✅ FIXED: Auto-cleanup enabled.
    """

    def __init__(self):
        """Initialize with DBManager and ensure stories folder exists."""
        self.db = get_db_manager()
        self._ensure_stories_folder()

    def _ensure_stories_folder(self):
        """Creates the stories folder if it doesn't exist."""
        if not os.path.exists(STORIES_FOLDER):
            os.makedirs(STORIES_FOLDER)

    def add_story(self, payload):
        """
        Adds a new story to the database using DBManager.
        Expected payload: {
            'username': 'user1',
            'filename': 'story.mp4',
            'content_type': 'photo'|'video'
        }
        """
        username = payload.get('username')
        filename = payload.get('filename')
        content_type = payload.get('content_type', 'photo')

        if not username or not filename:
            return {
                "status": "error",
                "message": "Missing username or filename"
            }

        # Generate unique filename
        timestamp = int(time.time())
        ext = os.path.splitext(filename)[FILE_EXTENSION_INDEX]
        unique_filename = f"{username}_{timestamp}{ext}"

        # Get current time as string
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # Use DBManager to add story
        result = self.db.add_story(
            username=username,
            content_type=content_type,
            content=filename,
            filename=unique_filename,
            timestamp=current_time
        )

        if result.get('status') == 'success':
            result['unique_filename'] = unique_filename

        return result

    def get_stories(self, payload):
        """
        Retrieves all stories from the last 24 hours using DBManager.
        Returns file paths for image/video stories.
        """
        # Calculate 24 hours ago
        twenty_four_hours_ago = (
            datetime.now() - timedelta(hours=HOURS_IN_A_DAY)
        ).strftime("%Y-%m-%d %H:%M:%S")

        # Use DBManager to get stories
        stories_data = self.db.get_stories(twenty_four_hours_ago)

        # Add file paths for media stories
        stories = []
        for story in stories_data:
            if story["content_type"] in ['image', 'video']:
                media_path = os.path.join(STORIES_FOLDER, story["content"])
                if os.path.exists(media_path):
                    story["file_path"] = media_path
                else:
                    story["file_path"] = None
            stories.append(story)

        return {"status": "success", "stories": stories}

    def delete_expired_stories(self):
        """
        Deletes stories older than 24 hours from both database and disk.
        Uses DBManager for database operations.
        """
        cutoff = (
                datetime.now() - timedelta(hours=HOURS_IN_A_DAY)
        ).strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Get expired stories before deleting (to delete files)
            expired_stories = self.db.get_stories("1900-01-01 00:00:00")

            # Filter to only expired ones and delete their files
            deleted_files = 0
            for story in expired_stories:
                if (
                        story["timestamp"] <= cutoff and
                        story["content_type"] in [
                            'image',
                            'video',
                        ]
                ):
                    # Try with 'content' field
                    file_path = os.path.join(
                        STORIES_FOLDER,
                        story.get("content", "")
                    )
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            deleted_files += 1
                            print(
                                f"[INFO] Deleted expired story file: "
                                f"{file_path}"
                            )
                        except Exception as e:
                            print(f"[WARN] Could not delete {file_path}: {e}")

                    # Also try with 'filename' field
                    file_path = os.path.join(
                        STORIES_FOLDER,
                        story.get("filename", "")
                    )
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            deleted_files += 1
                            print(
                                f"[INFO] Deleted expired story file: "
                                f"{file_path}"
                            )
                        except Exception as e:
                            print(f"[WARN] Could not delete {file_path}: {e}")

            # Use DBManager to delete expired stories from DB
            deleted_count = self.db.delete_old_stories(cutoff)

            if deleted_count > 0 or deleted_files > 0:
                print(
                    f"[INFO] Cleanup: Deleted {deleted_count} DB records "
                    f"and {deleted_files} files"
                )
            return {
                "status": "success",
                "message": f"Deleted {deleted_count} expired stories.",
                "deleted_db": deleted_count,
                "deleted_files": deleted_files
            }

        except Exception as e:
            print(f"[ERROR] delete_expired_stories: {e}")
            return {"status": "error", "message": f"Error: {e}"}

    def get_stories_from_folder(self):
        """
        Returns a combined list of story metadata from filesystem and database.
        This is a helper method for compatibility with existing code.
        ✅ FIXED: Now automatically cleans expired stories before returning.
        """
        try:
            # ✅ AUTO-CLEANUP: Delete expired stories first!
            print("[INFO] Running auto-cleanup of expired stories...")
            cleanup_result = self.delete_expired_stories()
            if cleanup_result.get("status") == "success":
                deleted = cleanup_result.get("deleted_db", 0)
                if deleted > 0:
                    print(f"[INFO] Cleaned up {deleted} expired stories")

            if not os.path.exists(STORY_FOLDER):
                os.makedirs(STORY_FOLDER)

            # Get files from folder
            files_in_folder = set(os.listdir(STORY_FOLDER))
            valid_extensions = [
                '.jpg', '.jpeg', '.png', '.bmp', '.gif',
                '.mp4', '.avi', '.mov'
            ]
            media_files = {
                f
                for f in files_in_folder
                if os.path.splitext(f)[
                       FILE_EXTENSION_INDEX
                   ].lower() in valid_extensions
            }
            stories = []

            # Get recent stories from DB (last 24 hours)
            cutoff = (
                datetime.now() - timedelta(hours=HOURS_IN_A_DAY)
            ).strftime("%Y-%m-%d %H:%M:%S")

            db_stories = self.db.get_stories(cutoff)

            # Add DB stories that exist in folder
            for story in db_stories:
                if story['filename'] in media_files:
                    stories.append({
                        'filename': story['filename'],
                        'username': story['username'],
                        'timestamp': story['timestamp'],
                        'content_type': story['content_type']
                    })

            # Add files that exist in folder but not in DB
            for filename in media_files:
                if not any(s['filename'] == filename for s in stories):
                    file_path = os.path.join(STORY_FOLDER, filename)
                    file_stat = os.stat(file_path)
                    file_timestamp = datetime.fromtimestamp(file_stat.st_mtime)
                    timestamp = file_timestamp.strftime('%Y-%m-%d %H:%M:%S')

                    # Check if file is within 24 hours
                    if file_timestamp > (
                            datetime.now() - timedelta(hours=HOURS_IN_A_DAY)
                    ):                        # Extract username from filename
                        username_parts = filename.split('_')
                        username = (
                            username_parts[FIRST_PART_INDEX]
                            if len(username_parts) > MIN_PARTS_WITH_SEPARATOR
                            else "Unknown"
                        )

                        # Determine content type
                        ext = Path(filename).suffix.lower()
                        content_type = (
                            "video"
                            if ext in ['.mp4', '.avi', '.mov']
                            else "photo"
                        )
                        stories.append({
                            'filename': filename,
                            'username': username,
                            'timestamp': timestamp,
                            'content_type': content_type
                        })

            # Sort by timestamp (newest first)
            stories.sort(key=lambda x: x['timestamp'], reverse=True)

            print(
                f"[INFO] Found {len(stories)} active stories "
                f"(within 24 hours)"
            )
            return {"status": "success", "stories": stories}

        except Exception as e:
            print(f"[ERROR] get_stories_from_folder: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e), "stories": []}

    def handle_request(self, request_type, payload):
        """Dispatches request to the matching handler."""
        if request_type == "ADD_STORY":
            return self.add_story(payload)
        elif request_type == "GET_STORIES":
            return self.get_stories_from_folder()
        elif request_type == "DELETE_EXPIRED_STORIES":
            return self.delete_expired_stories()
        else:
            return {"status": "error", "message": "Unknown request type."}
