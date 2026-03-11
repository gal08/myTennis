"""
Gal Haham
Request Methods Handler
Centralized request routing and handling logic
Handles video and story streaming with encryption
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
from Video_Player_Server import run_video_player_server
from story_player_server import run_story_player_server

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
    try:
        height, width = img.shape[:IMAGE_SHAPE_SLICE_2D]

        if height > width:
            new_height = THUMBNAIL_MAX_SIZE
            new_width = int(width * (THUMBNAIL_MAX_SIZE / height))
        else:
            new_width = THUMBNAIL_MAX_SIZE
            new_height = int(height * (THUMBNAIL_MAX_SIZE / width))

        return cv2.resize(img, (new_width, new_height))
    except:
        return None


def _encode_image_to_base64(img) -> str:
    try:
        _, buffer = cv2.imencode(JPEG_EXTENSION, img)
        return base64.b64encode(buffer).decode(ENCODING_FORMAT)
    except:
        return None


def _extract_image_thumbnail(file_path: str):
    try:
        img = cv2.imread(file_path)
        if img is None:
            return None

        resized_img = _resize_to_thumbnail(img)
        if resized_img is None:
            return None
        return _encode_image_to_base64(resized_img)
    except:
        return None


def _extract_video_thumbnail(file_path: str):
    try:
        cap = cv2.VideoCapture(file_path)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        return _encode_image_to_base64(frame)
    except:
        return None


def extract_thumbnail(file_path: str, file_type: str):
    try:
        if file_type == MEDIA_TYPE_IMAGE:
            return _extract_image_thumbnail(file_path)
        elif file_type == MEDIA_TYPE_VIDEO:
            return _extract_video_thumbnail(file_path)
        return None
    except:
        return None


def _add_video_to_list(media_data: list, filename: str, file_path: str):
    try:
        thumbnail = extract_thumbnail(file_path, MEDIA_TYPE_VIDEO)
        if thumbnail:
            media_data.append({
                'name': filename,
                'path': file_path,
                'thumbnail': thumbnail,
                'type': MEDIA_TYPE_VIDEO
            })
    except:
        pass


def _add_image_to_list(media_data: list, filename: str, file_path: str):
    try:
        thumbnail = extract_thumbnail(file_path, MEDIA_TYPE_IMAGE)
        if thumbnail:
            media_data.append({
                'name': filename,
                'path': file_path,
                'thumbnail': thumbnail,
                'type': MEDIA_TYPE_IMAGE
            })
    except:
        pass


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

        self.active_video_servers = {}
        self.video_servers_lock = threading.Lock()

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
                l1 = self.get_media_data()
                return {
                    "type": 'RES_GET_MEDIA',
                    "payload": l1
                }

            return self._create_error_response(MESSAGE_UNKNOWN_REQUEST)
        except:
            return self._create_error_response("Error routing request")

    def get_media_data(self) -> list:
        try:
            media_data = []

            if not os.path.exists(STORY_FOLDER):
                return media_data

            for file in os.listdir(STORY_FOLDER):
                file_lower = file.lower()
                file_path = os.path.join(STORY_FOLDER, file)

                if file_lower.endswith(VIDEO_EXTENSIONS):
                    _add_video_to_list(media_data, file, file_path)

                elif file_lower.endswith(IMAGE_EXTENSIONS):
                    _add_image_to_list(media_data, file, file_path)

            return media_data
        except:
            return []

    def handle_play_video(self, payload: dict) -> dict:
        try:
            video_title = payload.get(KEY_VIDEO_TITLE)

            if not video_title:
                return self._create_error_response(MESSAGE_VIDEO_NOT_PROVIDED)

            video_path = self._find_video_path(video_title)

            if not video_path:
                return self._create_error_response(MESSAGE_VIDEO_NOT_FOUND)

            print("Found video at:", video_path)

            with self.video_servers_lock:
                if video_title in self.active_video_servers:
                    server_thread = self.active_video_servers[video_title]
                    if server_thread.is_alive():
                        print("Video server already running")
                        return {
                            "status": "success",
                            "message": "Video server already running",
                            "port": 9999
                        }

            def start_video_server():
                try:
                    print("VIDEO SERVER Starting for", video_title)
                    run_video_player_server(video_path)
                    print("VIDEO SERVER Finished for", video_title)
                except:
                    pass
                finally:
                    with self.video_servers_lock:
                        if video_title in self.active_video_servers:
                            try:
                                del self.active_video_servers[video_title]
                            except:
                                pass

            video_thread = threading.Thread(
                target=start_video_server,
                daemon=True,
                name="VideoServer-" + video_title
            )
            video_thread.start()

            with self.video_servers_lock:
                self.active_video_servers[video_title] = video_thread

            print("Waiting for video server to initialize...")
            time.sleep(2.5)

            print("Video server started successfully")
            return {
                "status": "success",
                "message": MESSAGE_VIDEO_STREAM_STARTED,
                "port": 9999
            }

        except:
            return self._create_error_response(MESSAGE_VIDEO_STREAM_FAILED)

    def handle_play_story(self, payload: dict) -> dict:
        try:
            story_filename = payload.get(KEY_FILENAME)

            if not story_filename:
                return self._create_error_response(MESSAGE_STORY_NOT_PROVIDED)

            story_path = os.path.join(STORY_FOLDER, story_filename)

            if not os.path.exists(story_path):
                return self._create_error_response(MESSAGE_STORY_NOT_FOUND)

            def run_story():
                try:
                    run_story_player_server(story_filename)
                except:
                    pass

            thread = threading.Thread(
                target=run_story,
                daemon=True
            )
            thread.start()

            return self._create_success_response(MESSAGE_STORY_STREAM_STARTED)

        except:
            return self._create_error_response(MESSAGE_STORY_STREAM_FAILED)

    def handle_play_story_media(self, payload: dict) -> dict:
        try:
            filename = payload.get(KEY_FILENAME)
            story_path = os.path.join(STORY_FOLDER, filename)

            if not os.path.exists(story_path):
                return self._create_error_response(MESSAGE_FILE_NOT_FOUND)

            try:
                from VideoAudioServer import VideoAudioServer

                def start_stream_story():
                    try:
                        server = VideoAudioServer(
                            story_path,
                            host=DEFAULT_HOST,
                            port=VIDEO_STREAM_PORT
                        )
                        server.start()
                    except:
                        pass

                threading.Thread(
                    target=start_stream_story,
                    daemon=True
                ).start()

                return self._create_success_response(MESSAGE_STORY_STREAMING_STARTED)

            except:
                return self._create_error_response(MESSAGE_STORY_STREAM_FAILED)

        except:
            return self._create_error_response(MESSAGE_STORY_STREAM_FAILED)

    def get_stories_display_data(self) -> dict:
        try:
            return self._create_success_response(MESSAGE_STORIES_DISPLAYED)
        except:
            return self._create_error_response("Error getting stories")

    def get_videos_display_data(self) -> dict:
        try:
            return self._create_success_response(MESSAGE_VIDEOS_DISPLAYED)
        except:
            return self._create_error_response("Error getting videos")

    def handle_add_story(self, payload: dict) -> dict:
        try:
            if not self.story_upload_server_running:
                self.start_story_upload_server()
                time.sleep(STARTUP_DELAY_SECONDS)

            response = self.stories_handler.handle_request(
                REQUEST_ADD_STORY,
                payload
            )

            return response
        except:
            return self._create_error_response("Error adding story")

    def start_story_upload_server(self):
        try:
            if not self.story_upload_server_running:
                import story_saver_server

                def run_upload_server():
                    try:
                        print("Starting Story Upload Server (port 3333)...")
                        story_saver_server.run()
                    except:
                        pass

                self.story_upload_server_thread = threading.Thread(
                    target=run_upload_server,
                    daemon=True
                )
                self.story_upload_server_thread.start()
                self.story_upload_server_running = True
                time.sleep(0.5)
        except:
            pass

    def _find_video_path(self, video_title: str) -> str:
        try:
            VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']

            if not os.path.exists(VIDEO_FOLDER):
                return None

            for ext in VIDEO_EXTENSIONS:
                video_path = os.path.join(VIDEO_FOLDER, video_title + ext)
                if os.path.exists(video_path):
                    print("Found:", video_path)
                    return video_path

                video_path = os.path.join(VIDEO_FOLDER, video_title)
                if os.path.exists(video_path):
                    print("Found:", video_path)
                    return video_path

            try:
                for filename in os.listdir(VIDEO_FOLDER):
                    if filename.lower().startswith(video_title.lower()):
                        video_path = os.path.join(VIDEO_FOLDER, filename)
                        if os.path.isfile(video_path):
                            print("Found (fuzzy):", video_path)
                            return video_path
            except:
                pass

            print("Not found:", video_title)
            return None
        except:
            return None

    def _create_error_response(self, message: str) -> dict:
        try:
            return {KEY_STATUS: STATUS_ERROR, KEY_MESSAGE: message}
        except:
            return {"status": "error", "message": "Error"}

    def _create_success_response(self, message: str) -> dict:
        try:
            return {KEY_STATUS: STATUS_SUCCESS, KEY_MESSAGE: message}
        except:
            return {"status": "success", "message": "Success"}