"""
Gal Haham
Request Methods Handler
Centralized request routing and handling logic extracted from Server.py
This module handles all business logic for request processing.
"""
import base64
import json
import os
import time
import threading

import cv2

from Authication import Authentication
from Videos_Handler import VideosHandler
from Likes_Handler import LikesHandler
from Comments_Handler import CommentsHandler
from Stories_Handler import StoriesHandler
from Manger_commands import ManagerCommands
from Video_Player_Server import run_video_player_server
from story_player_server import run_story_player_server

# Request type constants
REQUEST_LOGIN = 'LOGIN'
REQUEST_SIGNUP = 'SIGNUP'
REQUEST_ADD_VIDEO = 'ADD_VIDEO'
REQUEST_GET_VIDEOS = 'GET_VIDEOS'
REQUEST_LIKE_VIDEO = 'LIKE_VIDEO'
REQUEST_GET_LIKES_COUNT = 'GET_LIKES_COUNT'
REQUEST_ADD_COMMENT = 'ADD_COMMENT'
REQUEST_GET_COMMENTS = 'GET_COMMENTS'
REQUEST_ADD_STORY = 'ADD_STORY'
REQUEST_GET_STORIES = 'GET_STORIES'
REQUEST_GET_ALL_USERS = 'GET_ALL_USERS'
REQUEST_PLAY_VIDEO = 'PLAY_VIDEO'
REQUEST_PLAY_STORY = 'PLAY_STORY'
REQUEST_PLAY_STORY_MEDIA = 'PLAY_STORY_MEDIA'
REQUEST_GET_IMAGES_OF_ALL_VIDEOS = 'GET_IMAGES_OF_ALL_VIDEOS'
REQUEST_GET_ALL_VIDEOS_GRID = 'GET_ALL_VIDEOS_GRID'
REQUEST_GET_MEDIA = 'GET_MEDIA'

# Response keys
KEY_TYPE = 'type'
KEY_PAYLOAD = 'payload'
KEY_VIDEO_TITLE = 'video_title'
KEY_FILENAME = 'filename'
KEY_STATUS = 'status'
KEY_MESSAGE = 'message'

# Status values
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

# Messages
MESSAGE_UNKNOWN_REQUEST = "Unknown request"
MESSAGE_VIDEO_NOT_PROVIDED = "Video title not provided"
MESSAGE_VIDEO_NOT_FOUND = "Video not found"
MESSAGE_VIDEO_STREAM_STARTED = "Video stream started"
MESSAGE_VIDEO_STREAM_FAILED = "Failed to start video server"
MESSAGE_STORY_NOT_PROVIDED = "Story filename not provided"
MESSAGE_STORY_NOT_FOUND = "Story not found"
MESSAGE_STORY_STREAM_STARTED = "Story stream started"
MESSAGE_STORY_STREAM_FAILED = "Failed to start story server"
MESSAGE_STORIES_DISPLAYED = "All stories displayed"
MESSAGE_VIDEOS_DISPLAYED = "Video grid display server started"
MESSAGE_STORY_STREAMING_STARTED = "Story streaming started"
MESSAGE_FILE_NOT_FOUND = "Story file not found"

# Folder paths
VIDEO_FOLDER = "videos"
STORY_FOLDER = "stories"

# Timing
STARTUP_DELAY_SECONDS = 1

# Server configuration
DEFAULT_HOST = '0.0.0.0'
VIDEO_STREAM_PORT = 9999

VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mkv', '.mov')
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

THUMBNAIL_MAX_SIZE = 200
IMAGE_SHAPE_SLICE_2D = 2

ENCODING_FORMAT = 'utf-8'
JPEG_EXTENSION = '.jpg'
ENSURE_ASCII_DISABLED = False

MEDIA_TYPE_IMAGE = 'image'
MEDIA_TYPE_VIDEO = 'video'


def _resize_to_thumbnail(img):
    """
    Resize image to thumbnail size while maintaining aspect ratio.

    Args:
        img: OpenCV image array

    Returns:
        Resized image
    """
    height, width = img.shape[:IMAGE_SHAPE_SLICE_2D]

    # Calculate new dimensions
    if height > width:
        new_height = THUMBNAIL_MAX_SIZE
        new_width = int(width * (THUMBNAIL_MAX_SIZE / height))
    else:
        new_width = THUMBNAIL_MAX_SIZE
        new_height = int(height * (THUMBNAIL_MAX_SIZE / width))

    return cv2.resize(img, (new_width, new_height))


def _encode_image_to_base64(img) -> str:
    """
    Encode image to base64 string.

    Args:
        img: OpenCV image array

    Returns:
        Base64 encoded string
    """
    _, buffer = cv2.imencode(JPEG_EXTENSION, img)
    return base64.b64encode(buffer).decode(ENCODING_FORMAT)


def _extract_image_thumbnail(file_path: str):
    """
    Extract thumbnail from image file.

    Args:
        file_path: Path to image file

    Returns:
        Base64 encoded thumbnail or None
    """
    img = cv2.imread(file_path)
    if img is None:
        return None

    # Resize image
    resized_img = _resize_to_thumbnail(img)

    # Encode to base64
    return _encode_image_to_base64(resized_img)


def _extract_video_thumbnail(file_path: str):
    """
    Extract first frame from video as thumbnail.

    Args:
        file_path: Path to video file

    Returns:
        Base64 encoded thumbnail or None
    """
    cap = cv2.VideoCapture(file_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None

    return _encode_image_to_base64(frame)


def extract_thumbnail(file_path: str, file_type: str):
    """
    Extract preview thumbnail from media file.
    REFACTORED: Split into separate methods for images and videos.

    Args:
        file_path: Path to media file
        file_type: Type of media ('image' or 'video')

    Returns:
        Base64 encoded thumbnail or None if extraction failed
    """
    if file_type == MEDIA_TYPE_IMAGE:
        return _extract_image_thumbnail(file_path)
    elif file_type == MEDIA_TYPE_VIDEO:
        return _extract_video_thumbnail(file_path)
    return None



def _add_video_to_list(
        media_data: list,
        filename: str,
        file_path: str
):
    """
    Add video to media list if thumbnail extraction succeeds.

    Args:
        media_data: List to append to
        filename: Name of file
        file_path: Full path to file
    """
    thumbnail = extract_thumbnail(file_path, MEDIA_TYPE_VIDEO)
    if thumbnail:
        media_data.append({
            'name': filename,
            'path': file_path,
            'thumbnail': thumbnail,
            'type': MEDIA_TYPE_VIDEO
        })


def _add_image_to_list(
        media_data: list,
        filename: str,
        file_path: str
):
    """
    Add image to media list if thumbnail extraction succeeds.

    Args:
        media_data: List to append to
        filename: Name of file
        file_path: Full path to file
    """
    thumbnail = extract_thumbnail(file_path, MEDIA_TYPE_IMAGE)
    if thumbnail:
        media_data.append({
            'name': filename,
            'path': file_path,
            'thumbnail': thumbnail,
            'type': MEDIA_TYPE_IMAGE
        })


class RequestMethodsHandler:
    """
    Centralized handler for all server request types.

    This class contains all the business logic for processing
    different types of requests, keeping the Server class clean
    and focused on network operations.
    """

    def __init__(self):
        """Initialize all request handlers."""
        # Initialize handlers
        self.auth_handler = Authentication()
        self.videos_handler = VideosHandler()
        self.likes_handler = LikesHandler()
        self.comments_handler = CommentsHandler()
        self.stories_handler = StoriesHandler()
        self.manager_commands = ManagerCommands()

        # Tracking for story upload server
        self.story_upload_server_running = False
        self.story_upload_server_thread = None

    def route_request(self, request_data: dict) -> dict:
        """
        Route request to appropriate handler.

        Args:
            request_data: Request dictionary

        Returns:
            Response dictionary
        """
        request_type = request_data.get(KEY_TYPE)
        payload = request_data.get(KEY_PAYLOAD, {})

        # Authentication
        if request_type in [REQUEST_LOGIN, REQUEST_SIGNUP]:
            return self.auth_handler.handle_request(request_type, payload)

        # Videos
        if request_type in [REQUEST_ADD_VIDEO, REQUEST_GET_VIDEOS]:
            return self.videos_handler.handle_request(request_type, payload)

        # Likes
        if request_type in [REQUEST_LIKE_VIDEO, REQUEST_GET_LIKES_COUNT]:
            return self.likes_handler.handle_request(request_type, payload)

        # Comments
        if request_type in [REQUEST_ADD_COMMENT, REQUEST_GET_COMMENTS]:
            return self.comments_handler.handle_request(request_type, payload)

        # Stories
        if request_type == REQUEST_ADD_STORY:
            return self.handle_add_story(payload)

        if request_type == REQUEST_GET_STORIES:
            return self.stories_handler.handle_request(request_type, payload)

        # Manager
        if request_type == REQUEST_GET_ALL_USERS:
            return self.manager_commands.handle_request(request_type, payload)

        # Playback
        if request_type == REQUEST_PLAY_VIDEO:
            return self.handle_play_video(payload)

        if request_type == REQUEST_PLAY_STORY:
            return self.handle_play_story(payload)

        if request_type == REQUEST_PLAY_STORY_MEDIA:
            return self.handle_play_story_media(payload)

        # Display
        if request_type == REQUEST_GET_IMAGES_OF_ALL_VIDEOS:
            return self.get_stories_display_data()

        if request_type == REQUEST_GET_ALL_VIDEOS_GRID:
            return self.get_videos_display_data()

        if request_type == REQUEST_GET_MEDIA:
            l1 = self.get_media_data()
            request_data = ({
                "type": 'RES_GET_MEDIA',
                "payload": l1
            })
            return request_data

        # Unknown
        return self._create_error_response(MESSAGE_UNKNOWN_REQUEST)


    def get_media_data(self) -> list:
        """
        Collect information about all media files in folder.

        Returns:
            List of dictionaries with media information:
                - name: filename
                - path: full path
                - thumbnail: base64 encoded preview
                - type: 'image' or 'video'
        """
        media_data = []

        # Scan folder for media files
        for file in os.listdir("stories"):
            file_lower = file.lower()
            file_path = os.path.join("stories", file)

            # Check if it's a video
            if file_lower.endswith(VIDEO_EXTENSIONS):
                _add_video_to_list(media_data, file, file_path)

            # Check if it's an image
            elif file_lower.endswith(IMAGE_EXTENSIONS):
                _add_image_to_list(media_data, file, file_path)

        return media_data



    def handle_play_video(self, payload: dict) -> dict:
        """
        Handle PLAY_VIDEO request.

        Args:
            payload: Request payload with video_title

        Returns:
            Response dictionary
        """
        import os

        video_title = payload.get(KEY_VIDEO_TITLE)

        if not video_title:
            return self._create_error_response(MESSAGE_VIDEO_NOT_PROVIDED)

        video_path = os.path.join(VIDEO_FOLDER, video_title)

        if not os.path.exists(video_path):
            return self._create_error_response(
                f"{MESSAGE_VIDEO_NOT_FOUND}: {video_title}"
            )

        try:
            thread = threading.Thread(
                target=run_video_player_server,
                args=(video_path,),
                daemon=True
            )
            thread.start()

            return self._create_success_response(MESSAGE_VIDEO_STREAM_STARTED)

        except Exception as e:
            return self._create_error_response(
                f"{MESSAGE_VIDEO_STREAM_FAILED}: {e}"
            )

    def handle_play_story(self, payload: dict) -> dict:
        """
        Handle PLAY_STORY request (old mechanism).

        Args:
            payload: Request payload with filename

        Returns:
            Response dictionary
        """
        import os

        story_filename = payload.get(KEY_FILENAME)

        if not story_filename:
            return self._create_error_response(MESSAGE_STORY_NOT_PROVIDED)

        story_path = os.path.join(STORY_FOLDER, story_filename)

        if not os.path.exists(story_path):
            return self._create_error_response(
                f"{MESSAGE_STORY_NOT_FOUND}: {story_filename}"
            )

        try:
            thread = threading.Thread(
                target=run_story_player_server,
                args=(story_filename,),
                daemon=True
            )
            thread.start()

            return self._create_success_response(MESSAGE_STORY_STREAM_STARTED)

        except Exception as e:
            return self._create_error_response(
                f"{MESSAGE_STORY_STREAM_FAILED}: {e}"
            )

    def handle_play_story_media(self, payload: dict) -> dict:
        """
        Handle PLAY_STORY_MEDIA request (WX streaming version).

        Args:
            payload: Request payload with filename

        Returns:
            Response dictionary
        """
        import os

        filename = payload.get(KEY_FILENAME)
        story_path = os.path.join(STORY_FOLDER, filename)

        if not os.path.exists(story_path):
            return self._create_error_response(
                f"{MESSAGE_FILE_NOT_FOUND}: {filename}"
            )

        try:
            from VideoAudioServer import VideoAudioServer

            def start_stream_story():
                server = VideoAudioServer(
                    story_path,
                    host=DEFAULT_HOST,
                    port=VIDEO_STREAM_PORT
                )
                server.start()

            threading.Thread(
                target=start_stream_story,
                daemon=True
            ).start()

            return self._create_success_response(
                MESSAGE_STORY_STREAMING_STARTED
            )

        except Exception as e:
            return self._create_error_response(str(e))

    def get_stories_display_data(self) -> dict:
        """Return success - stories server already running."""
        return self._create_success_response(MESSAGE_STORIES_DISPLAYED)

    def get_videos_display_data(self) -> dict:
        """Return success - video server already running."""
        return self._create_success_response(MESSAGE_VIDEOS_DISPLAYED)

    def handle_add_story(self, payload: dict) -> dict:
        """
        Handle ADD_STORY request.

        Args:
            payload: Story data

        Returns:
            Response dictionary
        """
        # Ensure upload server is running
        if not self.story_upload_server_running:
            self.start_story_upload_server()
            time.sleep(STARTUP_DELAY_SECONDS)

        # Process story metadata
        response = self.stories_handler.handle_request(
            REQUEST_ADD_STORY,
            payload
        )

        return response

    def start_story_upload_server(self):
        """Start story upload server (port 3333)."""
        if not self.story_upload_server_running:
            import story_saver_server

            def run_upload_server():
                try:
                    print("Starting Story Upload Server (port 3333)...")
                    story_saver_server.run()
                except Exception as e:
                    print(f"[ERROR] Story upload server: {e}")

            self.story_upload_server_thread = threading.Thread(
                target=run_upload_server,
                daemon=True
            )
            self.story_upload_server_thread.start()
            self.story_upload_server_running = True
            time.sleep(0.5)

    def _create_error_response(self, message: str) -> dict:
        """
        Create error response.

        Args:
            message: Error message

        Returns:
            Error response dictionary
        """
        return {KEY_STATUS: STATUS_ERROR, KEY_MESSAGE: message}

    def _create_success_response(self, message: str) -> dict:
        """
        Create success response.

        Args:
            message: Success message

        Returns:
            Success response dictionary
        """
        return {KEY_STATUS: STATUS_SUCCESS, KEY_MESSAGE: message}
