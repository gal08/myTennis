"""
Gal Haham
Request Methods Handler
Centralized request routing and handling logic
REFACTORED: Both videos and stories use single-port + ticket system.
            No more per-request port allocation.
            Videos  → port 9999  (ensure_video_server_running)
            Stories → port 6001  (ensure_story_server_running)
"""
import threading
import time
import os
import base64
import cv2

from Authication import Authentication
from Videos_Handler import VideosHandler
from Likes_Handler import LikesHandler
from Comments_Handler import CommentsHandler
from Stories_Handler import StoriesHandler
from Manger_commands import ManagerCommands
from VideoAudioServer import ensure_video_server_running
from story_player_server import ensure_story_server_running

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

KEY_TYPE = 'type'
KEY_PAYLOAD = 'payload'
KEY_VIDEO_TITLE = 'video_title'
KEY_FILENAME = 'filename'
KEY_STATUS = 'status'
KEY_MESSAGE = 'message'

STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

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

VIDEO_FOLDER = "videos"
STORY_FOLDER = "stories"

STARTUP_DELAY_SECONDS = 1

DEFAULT_HOST = '0.0.0.0'
VIDEO_STREAM_PORT = 9999
STORY_STREAM_PORT = 6001

VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mkv', '.mov')
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

THUMBNAIL_MAX_SIZE = 200
IMAGE_SHAPE_SLICE_2D = 2

ENCODING_FORMAT = 'utf-8'
JPEG_EXTENSION = '.jpg'

MEDIA_TYPE_IMAGE = 'image'
MEDIA_TYPE_VIDEO = 'video'


class RequestMethodsHandler:

    def __init__(self):
        self.auth_handler = Authentication()
        self.videos_handler = VideosHandler()
        self.likes_handler = LikesHandler()
        self.comments_handler = CommentsHandler()
        self.stories_handler = StoriesHandler()
        self.manager_commands = ManagerCommands()

        self.story_upload_server_running = False
        self.story_upload_server_thread = None

    # ── Router ────────────────────────────────────────────────────────────────

    def route_request(self, request_data: dict) -> dict:
        try:
            request_type = request_data.get(KEY_TYPE)
            payload = request_data.get(KEY_PAYLOAD, {})

            print("Routing request type:", request_type)

            if request_type in [REQUEST_LOGIN, REQUEST_SIGNUP]:
                return self.auth_handler.handle_request(request_type, payload)

            if request_type in [REQUEST_ADD_VIDEO, REQUEST_GET_VIDEOS]:
                return self.videos_handler.handle_request(request_type, payload)

            if request_type in [REQUEST_LIKE_VIDEO, REQUEST_GET_LIKES_COUNT]:
                return self.likes_handler.handle_request(request_type, payload)

            if request_type in [REQUEST_ADD_COMMENT, REQUEST_GET_COMMENTS]:
                return self.comments_handler.handle_request(request_type, payload)

            if request_type == REQUEST_ADD_STORY:
                return self.handle_add_story(payload)

            if request_type == REQUEST_GET_STORIES:
                return self.stories_handler.handle_request(request_type, payload)

            if request_type == REQUEST_GET_ALL_USERS:
                return self.manager_commands.handle_request(request_type, payload)

            if request_type == REQUEST_PLAY_VIDEO:
                return self.handle_play_video(payload)

            if request_type == REQUEST_PLAY_STORY:
                return self.handle_play_story(payload)

            if request_type == REQUEST_PLAY_STORY_MEDIA:
                return self.handle_play_story_media(payload)

            if request_type == REQUEST_GET_IMAGES_OF_ALL_VIDEOS:
                return self.get_stories_display_data()

            if request_type == REQUEST_GET_ALL_VIDEOS_GRID:
                return self.get_videos_display_data()

            if request_type == REQUEST_GET_MEDIA:
                return {"type": 'RES_GET_MEDIA', "payload": self.get_media_data()}

            return self._create_error_response(MESSAGE_UNKNOWN_REQUEST)
        except Exception:
            return self._create_error_response("Error routing request")

    # ── Thumbnail helpers ─────────────────────────────────────────────────────

    def _resize_to_thumbnail(self, img):
        try:
            height, width = img.shape[:IMAGE_SHAPE_SLICE_2D]
            if height > width:
                new_height = THUMBNAIL_MAX_SIZE
                new_width = int(width * (THUMBNAIL_MAX_SIZE / height))
            else:
                new_width = THUMBNAIL_MAX_SIZE
                new_height = int(height * (THUMBNAIL_MAX_SIZE / width))
            return cv2.resize(img, (new_width, new_height))
        except Exception:
            return None

    def _encode_image_to_base64(self, img) -> str:
        try:
            _, buffer = cv2.imencode(JPEG_EXTENSION, img)
            return base64.b64encode(buffer).decode(ENCODING_FORMAT)
        except Exception:
            return None

    def _extract_image_thumbnail(self, file_path: str):
        try:
            img = cv2.imread(file_path)
            if img is None:
                return None
            resized = self._resize_to_thumbnail(img)
            return self._encode_image_to_base64(resized) if resized is not None else None
        except Exception:
            return None

    def _extract_video_thumbnail(self, file_path: str):
        try:
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            cap.release()
            return self._encode_image_to_base64(frame) if ret else None
        except Exception:
            return None

    def extract_thumbnail(self, file_path: str, file_type: str):
        try:
            if file_type == MEDIA_TYPE_IMAGE:
                return self._extract_image_thumbnail(file_path)
            elif file_type == MEDIA_TYPE_VIDEO:
                return self._extract_video_thumbnail(file_path)
            return None
        except Exception:
            return None

    # ── Media list helpers ────────────────────────────────────────────────────

    def _add_video_to_list(self, media_data: list, filename: str, file_path: str):
        try:
            thumbnail = self.extract_thumbnail(file_path, MEDIA_TYPE_VIDEO)
            if thumbnail:
                media_data.append({'name': filename, 'path': file_path,
                                   'thumbnail': thumbnail, 'type': MEDIA_TYPE_VIDEO})
        except Exception:
            pass

    def _add_image_to_list(self, media_data: list, filename: str, file_path: str):
        try:
            thumbnail = self.extract_thumbnail(file_path, MEDIA_TYPE_IMAGE)
            if thumbnail:
                media_data.append({'name': filename, 'path': file_path,
                                   'thumbnail': thumbnail, 'type': MEDIA_TYPE_IMAGE})
        except Exception:
            pass

    # ── Media data ────────────────────────────────────────────────────────────

    def get_media_data(self) -> list:
        try:
            media_data = []
            if not os.path.exists(STORY_FOLDER):
                return media_data

            for file in os.listdir(STORY_FOLDER):
                file_lower = file.lower()
                file_path = os.path.join(STORY_FOLDER, file)
                if file_lower.endswith(VIDEO_EXTENSIONS):
                    self._add_video_to_list(media_data, file, file_path)
                elif file_lower.endswith(IMAGE_EXTENSIONS):
                    self._add_image_to_list(media_data, file, file_path)
            return media_data
        except Exception:
            return []

    # ── Video handling ────────────────────────────────────────────────────────

    def handle_play_video(self, payload: dict) -> dict:
        """
        Returns a one-time ticket the client uses to identify which video
        to stream. All videos share a single server on port 9999.
        """
        try:
            video_title = payload.get(KEY_VIDEO_TITLE)

            if not video_title:
                return self._create_error_response(MESSAGE_VIDEO_NOT_PROVIDED)

            video_path = self._find_video_path(video_title)
            if not video_path:
                return self._create_error_response(MESSAGE_VIDEO_NOT_FOUND)

            print(f"[Methods] Creating streaming ticket for video → {video_path}")

            result = ensure_video_server_running(video_path)
            port   = result.get("port")
            ticket = result.get("ticket")

            if not port or not ticket:
                return self._create_error_response(MESSAGE_VIDEO_STREAM_FAILED)

            print(f"[Methods] Video '{video_title}' ticket={ticket} port={port}")
            return {
                KEY_STATUS: STATUS_SUCCESS,
                KEY_MESSAGE: MESSAGE_VIDEO_STREAM_STARTED,
                "port": port,
                "ticket": ticket,
            }

        except Exception as e:
            print(f"[Methods] handle_play_video error: {e}")
            return self._create_error_response(MESSAGE_VIDEO_STREAM_FAILED)

    def _find_video_path(self, video_title: str) -> str:
        try:
            extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']

            if not os.path.exists(VIDEO_FOLDER):
                return None

            for ext in extensions:
                path = os.path.join(VIDEO_FOLDER, video_title + ext)
                if os.path.exists(path):
                    return path

            path = os.path.join(VIDEO_FOLDER, video_title)
            if os.path.exists(path):
                return path

            for filename in os.listdir(VIDEO_FOLDER):
                if filename.lower().startswith(video_title.lower()):
                    path = os.path.join(VIDEO_FOLDER, filename)
                    if os.path.isfile(path):
                        return path

            return None
        except Exception:
            return None

    # ── Story handling ────────────────────────────────────────────────────────

    def handle_play_story(self, payload: dict) -> dict:
        """
        Returns a one-time ticket the client uses to identify which story
        to stream. All stories share a single server on port 6001.
        """
        try:
            story_filename = payload.get(KEY_FILENAME)
            if not story_filename:
                return self._create_error_response(MESSAGE_STORY_NOT_PROVIDED)

            story_path = os.path.join(STORY_FOLDER, story_filename)
            if not os.path.exists(story_path):
                return self._create_error_response(MESSAGE_STORY_NOT_FOUND)

            print(f"[Methods] Creating streaming ticket for story → {story_path}")

            result = ensure_story_server_running(story_path)
            port   = result.get("port")
            ticket = result.get("ticket")

            if not port or not ticket:
                return self._create_error_response(MESSAGE_STORY_STREAM_FAILED)

            print(f"[Methods] Story '{story_filename}' ticket={ticket} port={port}")
            return {
                KEY_STATUS: STATUS_SUCCESS,
                KEY_MESSAGE: MESSAGE_STORY_STREAM_STARTED,
                "port": port,
                "ticket": ticket,
            }

        except Exception as e:
            print(f"[Methods] handle_play_story error: {e}")
            return self._create_error_response(MESSAGE_STORY_STREAM_FAILED)

    def handle_play_story_media(self, payload: dict) -> dict:
        try:
            filename = payload.get(KEY_FILENAME)
            story_path = os.path.join(STORY_FOLDER, filename)

            if not os.path.exists(story_path):
                return self._create_error_response(MESSAGE_FILE_NOT_FOUND)

            result = ensure_story_server_running(story_path)
            port   = result.get("port")
            ticket = result.get("ticket")

            if not port or not ticket:
                return self._create_error_response(MESSAGE_STORY_STREAM_FAILED)

            return {
                KEY_STATUS: STATUS_SUCCESS,
                KEY_MESSAGE: MESSAGE_STORY_STREAMING_STARTED,
                "port": port,
                "ticket": ticket,
            }
        except Exception:
            return self._create_error_response(MESSAGE_STORY_STREAM_FAILED)

    def get_stories_display_data(self) -> dict:
        try:
            return self._create_success_response(MESSAGE_STORIES_DISPLAYED)
        except Exception:
            return self._create_error_response("Error getting stories")

    def get_videos_display_data(self) -> dict:
        try:
            return self._create_success_response(MESSAGE_VIDEOS_DISPLAYED)
        except Exception:
            return self._create_error_response("Error getting videos")

    # ── Story upload server ───────────────────────────────────────────────────

    def handle_add_story(self, payload: dict) -> dict:
        try:
            if not self.story_upload_server_running:
                self.start_story_upload_server()
                time.sleep(STARTUP_DELAY_SECONDS)
            return self.stories_handler.handle_request(REQUEST_ADD_STORY, payload)
        except Exception:
            return self._create_error_response("Error adding story")

    def _run_story_upload_server(self):
        try:
            import story_saver_server
            print("Starting Story Upload Server (port 3333)...")
            story_saver_server.run()
        except Exception:
            pass

    def start_story_upload_server(self):
        try:
            if not self.story_upload_server_running:
                self.story_upload_server_thread = threading.Thread(
                    target=self._run_story_upload_server,
                    daemon=True
                )
                self.story_upload_server_thread.start()
                self.story_upload_server_running = True
                time.sleep(0.5)
        except Exception:
            pass

    # ── Response builders ─────────────────────────────────────────────────────

    def _create_error_response(self, message: str) -> dict:
        return {KEY_STATUS: STATUS_ERROR, KEY_MESSAGE: message}

    def _create_success_response(self, message: str) -> dict:
        return {KEY_STATUS: STATUS_SUCCESS, KEY_MESSAGE: message}