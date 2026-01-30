"""
Gal Haham
Story management system with 24-hour expiration.
Handles story creation, retrieval, and automatic cleanup of expired content.
NOW USES DBManager for all database operations.
"""
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from Db_manager import get_db_manager

# Folder paths
STORIES_FOLDER = "stories"
STORY_FOLDER = "stories"

# Time constants
HOURS_IN_A_DAY = 24

# Array indices
FILE_EXTENSION_INDEX = 1
FIRST_PART_INDEX = 0

# Minimum counts
MIN_PARTS_WITH_SEPARATOR = 1
ZERO_DELETED_FILES = 0
ZERO_DELETED_STORIES = 0

# Content types
CONTENT_TYPE_IMAGE = 'image'
CONTENT_TYPE_VIDEO = 'video'
CONTENT_TYPE_PHOTO = 'photo'

# Status values
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

# Messages
MSG_MISSING_DATA = "Missing username or filename"
MSG_ERROR_PREFIX = "Error: "
MSG_DELETED_TEMPLATE = "Deleted {} expired stories."
MSG_CLEANUP_INFO = "[INFO] Cleanup: Deleted {} DB records and {} files"
MSG_CLEANUP_STARTING = "[INFO] Running auto-cleanup of expired stories..."
MSG_CLEANUP_COMPLETED = "[INFO] Cleaned up {} expired stories"
MSG_DELETED_FILE = "[INFO] Deleted expired story file: {}"
MSG_DELETE_WARNING = "[WARN] Could not delete {}: {}"
MSG_ERROR_DELETE = "[ERROR] delete_expired_stories: {}"
MSG_ERROR_GET_STORIES = "[ERROR] get_stories_from_folder: {}"
MSG_FOUND_STORIES = "[INFO] Found {} active stories (within 24 hours)"
MSG_UNKNOWN_REQUEST = "Unknown request type."

# Database query dates
EARLIEST_DATE = "1900-01-01 00:00:00"

# Date format
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# File extensions
EXT_JPG = '.jpg'
EXT_JPEG = '.jpeg'
EXT_PNG = '.png'
EXT_BMP = '.bmp'
EXT_GIF = '.gif'
EXT_MP4 = '.mp4'
EXT_AVI = '.avi'
EXT_MOV = '.mov'

# Valid extension lists
IMAGE_EXTENSIONS = [EXT_JPG, EXT_JPEG, EXT_PNG, EXT_BMP, EXT_GIF]
VIDEO_EXTENSIONS = [EXT_MP4, EXT_AVI, EXT_MOV]

# Dictionary keys
KEY_USERNAME = 'username'
KEY_FILENAME = 'filename'
KEY_CONTENT_TYPE = 'content_type'
KEY_STATUS = 'status'
KEY_MESSAGE = 'message'
KEY_CONTENT = 'content'
KEY_FILE_PATH = 'file_path'
KEY_TIMESTAMP = 'timestamp'
KEY_UNIQUE_FILENAME = 'unique_filename'
KEY_DELETED_DB = 'deleted_db'
KEY_DELETED_FILES = 'deleted_files'
KEY_STORIES = 'stories'

# Request types
REQUEST_ADD_STORY = "ADD_STORY"
REQUEST_GET_STORIES = "GET_STORIES"
REQUEST_DELETE_EXPIRED = "DELETE_EXPIRED_STORIES"

# Default values
DEFAULT_CONTENT_TYPE = 'photo'
DEFAULT_USERNAME = "Unknown"
DEFAULT_DELETED_COUNT = 0

# Comparison values
NO_DELETIONS = 0
SORT_REVERSE = True


class StoriesHandler:
    """
    Handles ADD_STORY and GET_STORIES operations with DBManager.
    Stories expire after 24 hours.
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
        username = payload.get(KEY_USERNAME)
        filename = payload.get(KEY_FILENAME)
        content_type = payload.get(KEY_CONTENT_TYPE, DEFAULT_CONTENT_TYPE)

        if not username or not filename:
            return {
                KEY_STATUS: STATUS_ERROR,
                KEY_MESSAGE: MSG_MISSING_DATA
            }

        # Generate unique filename
        timestamp = int(time.time())
        ext = os.path.splitext(filename)[FILE_EXTENSION_INDEX]
        unique_filename = f"{username}_{timestamp}{ext}"

        # Get current time as string
        current_time = time.strftime(DATE_FORMAT)

        # Use DBManager to add story
        result = self.db.add_story(
            username=username,
            content_type=content_type,
            content=filename,
            filename=unique_filename,
            timestamp=current_time
        )

        if result.get(KEY_STATUS) == STATUS_SUCCESS:
            result[KEY_UNIQUE_FILENAME] = unique_filename

        return result

    def get_stories(self, payload):
        """
        Retrieves all stories from the last 24 hours using DBManager.
        Returns file paths for image/video stories.
        """
        # Calculate 24 hours ago
        twenty_four_hours_ago = (
            datetime.now() - timedelta(hours=HOURS_IN_A_DAY)
        ).strftime(DATE_FORMAT)

        # Use DBManager to get stories
        stories_data = self.db.get_stories(twenty_four_hours_ago)

        # Add file paths for media stories
        stories = []
        for story in stories_data:
            if story[KEY_CONTENT_TYPE] in (
                    CONTENT_TYPE_IMAGE,
                    CONTENT_TYPE_VIDEO,
            ):
                media_path = os.path.join(
                    STORIES_FOLDER,
                    story[KEY_CONTENT],
                )
                if os.path.exists(media_path):
                    story[KEY_FILE_PATH] = media_path
                else:
                    story[KEY_FILE_PATH] = None
            stories.append(story)
        return {KEY_STATUS: STATUS_SUCCESS, KEY_STORIES: stories}

    def delete_expired_stories(self):
        """
        Deletes stories older than 24 hours from both database and disk.
        Uses DBManager for database operations.
        """
        cutoff = (
                datetime.now() - timedelta(hours=HOURS_IN_A_DAY)
        ).strftime(DATE_FORMAT)

        try:
            # Get expired stories before deleting (to delete files)
            expired_stories = self.db.get_stories(EARLIEST_DATE)

            # Filter to only expired ones and delete their files
            deleted_files = ZERO_DELETED_FILES
            for story in expired_stories:
                if (
                        story[KEY_TIMESTAMP] <= cutoff and
                        story[KEY_CONTENT_TYPE] in [
                            CONTENT_TYPE_IMAGE,
                            CONTENT_TYPE_VIDEO,
                        ]
                ):
                    # Try with 'content' field
                    file_path = os.path.join(
                        STORIES_FOLDER,
                        story.get(KEY_CONTENT, "")
                    )
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            deleted_files += 1
                            print(MSG_DELETED_FILE.format(file_path))
                        except Exception as e:
                            print(MSG_DELETE_WARNING.format(file_path, e))

                    # Also try with 'filename' field
                    file_path = os.path.join(
                        STORIES_FOLDER,
                        story.get(KEY_FILENAME, "")
                    )
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            deleted_files += 1
                            print(MSG_DELETED_FILE.format(file_path))
                        except Exception as e:
                            print(MSG_DELETE_WARNING.format(file_path, e))

            # Use DBManager to delete expired stories from DB
            deleted_count = self.db.delete_old_stories(cutoff)

            if deleted_count > NO_DELETIONS or deleted_files > NO_DELETIONS:
                print(MSG_CLEANUP_INFO.format(deleted_count, deleted_files))

            return {
                KEY_STATUS: STATUS_SUCCESS,
                KEY_MESSAGE: MSG_DELETED_TEMPLATE.format(deleted_count),
                KEY_DELETED_DB: deleted_count,
                KEY_DELETED_FILES: deleted_files
            }

        except Exception as e:
            print(MSG_ERROR_DELETE.format(e))
            return {
                KEY_STATUS: STATUS_ERROR,
                KEY_MESSAGE: f"{MSG_ERROR_PREFIX}{e}",
            }

    def get_stories_from_folder(self):
        """
        Returns a combined list of story metadata from filesystem and database.
        This is a helper method for compatibility with existing code.
        """
        try:
            print(MSG_CLEANUP_STARTING)
            cleanup_result = self.delete_expired_stories()
            if cleanup_result.get(KEY_STATUS) == STATUS_SUCCESS:
                deleted = cleanup_result.get(
                    KEY_DELETED_DB,
                    DEFAULT_DELETED_COUNT,
                )
                if deleted > NO_DELETIONS:
                    print(MSG_CLEANUP_COMPLETED.format(deleted))

            if not os.path.exists(STORY_FOLDER):
                os.makedirs(STORY_FOLDER)

            # Get files from folder
            files_in_folder = set(os.listdir(STORY_FOLDER))
            valid_extensions = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS
            media_files = {
                f
                for f in files_in_folder
                if (
                        os.path.splitext(f)[FILE_EXTENSION_INDEX].lower()
                        in valid_extensions
                )
            }
            stories = []

            # Get recent stories from DB (last 24 hours)
            cutoff = (
                datetime.now() - timedelta(hours=HOURS_IN_A_DAY)
            ).strftime(DATE_FORMAT)

            db_stories = self.db.get_stories(cutoff)

            # Add DB stories that exist in folder
            for story in db_stories:
                if story[KEY_FILENAME] in media_files:
                    stories.append({
                        KEY_FILENAME: story[KEY_FILENAME],
                        KEY_USERNAME: story[KEY_USERNAME],
                        KEY_TIMESTAMP: story[KEY_TIMESTAMP],
                        KEY_CONTENT_TYPE: story[KEY_CONTENT_TYPE]
                    })

            # Add files that exist in folder but not in DB
            for filename in media_files:
                if not any(s[KEY_FILENAME] == filename for s in stories):
                    file_path = os.path.join(STORY_FOLDER, filename)
                    file_stat = os.stat(file_path)
                    file_timestamp = datetime.fromtimestamp(file_stat.st_mtime)
                    timestamp = file_timestamp.strftime(DATE_FORMAT)

                    # Check if file is within 24 hours
                    if file_timestamp > (
                            datetime.now() - timedelta(hours=HOURS_IN_A_DAY)
                    ):
                        # Extract username from filename
                        username_parts = filename.split('_')
                        username = (
                            username_parts[FIRST_PART_INDEX]
                            if len(username_parts) > MIN_PARTS_WITH_SEPARATOR
                            else DEFAULT_USERNAME
                        )

                        # Determine content type
                        ext = Path(filename).suffix.lower()
                        content_type = (
                            CONTENT_TYPE_VIDEO
                            if ext in VIDEO_EXTENSIONS
                            else CONTENT_TYPE_PHOTO
                        )
                        stories.append({
                            KEY_FILENAME: filename,
                            KEY_USERNAME: username,
                            KEY_TIMESTAMP: timestamp,
                            KEY_CONTENT_TYPE: content_type
                        })

            # Sort by timestamp (newest first)
            stories.sort(key=lambda x: x[KEY_TIMESTAMP], reverse=SORT_REVERSE)

            print(MSG_FOUND_STORIES.format(len(stories)))
            return {KEY_STATUS: STATUS_SUCCESS, KEY_STORIES: stories}

        except Exception as e:
            print(MSG_ERROR_GET_STORIES.format(e))
            import traceback
            traceback.print_exc()
            return {
                KEY_STATUS: STATUS_ERROR,
                KEY_MESSAGE: str(e),
                KEY_STORIES: [],
            }

    def handle_request(self, request_type, payload):
        """Dispatches request to the matching handler."""
        if request_type == REQUEST_ADD_STORY:
            return self.add_story(payload)
        elif request_type == REQUEST_GET_STORIES:
            return self.get_stories_from_folder()
        elif request_type == REQUEST_DELETE_EXPIRED:
            return self.delete_expired_stories()
        else:
            return {KEY_STATUS: STATUS_ERROR, KEY_MESSAGE: MSG_UNKNOWN_REQUEST}