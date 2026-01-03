"""
Gal Haham
Main Tennis Social server application.
Routes client requests, manages handlers, and coordinates
video/story streaming servers.
REFACTORED: Constants extracted, methods split, brief docs.
"""
import socket
import json
import os
import cv2
import base64
from pathlib import Path
import time
import threading

import story_saver_server
from Protocol import Protocol
from Authication import Authentication
from Videos_Handler import VideosHandler
from Likes_Handler import LikesHandler
from Comments_Handler import CommentsHandler
from Stories_Handler import StoriesHandler
from Manger_commands import ManagerCommands
from Video_Player_Server import run_video_player_server
from story_player_server import run_story_player_server
from handle_show_all_stories import run as run_stories_display_server

# Import for video grid display
try:
    from handle_show_all_videos import run as run_videos_display_server
except ImportError:
    run_videos_display_server = None

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000
STORY_UPLOAD_PORT = 3333
VIDEO_STREAM_PORT = 9999
MAX_PENDING_CONNECTIONS = 5
SOCKET_REUSE_ADDRESS = 1

VIDEO_FOLDER = "videos"
STORY_FOLDER = "stories"
DB_FILE = 'users.db'

PREVIEW_LENGTH = 200
SEPARATOR_LENGTH = 50
SEPARATOR_CHAR = "="

STARTUP_DELAY_SECONDS = 1

JSON_START_CHAR = '{'
NOT_FOUND_INDEX = -1

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
MESSAGE_VIDEO_DISPLAY_UNAVAILABLE = "Video display server not available"
MESSAGE_STORY_STREAMING_STARTED = "Story streaming started"
MESSAGE_FILE_NOT_FOUND = "Story file not found"

KEY_TYPE = 'type'
KEY_PAYLOAD = 'payload'
KEY_VIDEO_TITLE = 'video_title'
KEY_FILENAME = 'filename'
KEY_STATUS = 'status'
KEY_MESSAGE = 'message'


class Server:
    """Main Tennis Social server."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        """
        Initialize server.

        Args:
            host: Server hostname
            port: Server port
        """
        self.host = host
        self.port = port
        self.running = False
        self.video_server_thread = None
        self.story_server_thread = None
        self.story_upload_server_thread = None
        self.story_upload_server_running = False

        # Initialize handlers
        self.auth_handler = Authentication()
        self.videos_handler = VideosHandler()
        self.likes_handler = LikesHandler()
        self.comments_handler = CommentsHandler()
        self.stories_handler = StoriesHandler()
        self.manager_commands = ManagerCommands()

        # Ensure folders
        os.makedirs(VIDEO_FOLDER, exist_ok=True)
        os.makedirs(STORY_FOLDER, exist_ok=True)

    def start(self):
        """Start the main TCP server."""
        self._create_server_socket()
        self._print_startup_banner()
        self.start_story_upload_server()

        try:
            self._run_server_loop()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"Server error: {e}")
            self.stop()

    def _create_server_socket(self):
        """Create and configure server socket."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            SOCKET_REUSE_ADDRESS
        )
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MAX_PENDING_CONNECTIONS)
        self.running = True

    def _print_startup_banner(self):
        """Print server startup information."""
        separator = SEPARATOR_CHAR * SEPARATOR_LENGTH
        print(separator)
        print("🎾 Tennis Social Server")
        print(separator)
        print(f"Main Server: {self.host}: {self.port}")
        print(f"Story Upload: {self.host}: {STORY_UPLOAD_PORT}")
        print(separator)
        print("Server is ready and waiting for clients...")
        print(separator)

    def _run_server_loop(self):
        """Main server loop - accept and handle clients."""
        while self.running:
            client_socket, addr = self.server_socket.accept()

            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket,),
                daemon=True
            )
            client_thread.start()

    def stop(self):
        """Stop the server."""
        self.running = False
        self.server_socket.close()
        print("\nServer stopped.")

    def start_story_upload_server(self):
        """Start story upload server (port 3333)."""
        if not self.story_upload_server_running:
            def run_upload_server():
                try:
                    story_saver_server.run()
                except Exception as e:
                    print(f"[ERROR] Story upload server: {e}")

            self.story_upload_server_thread = threading.Thread(
                target=run_upload_server,
                daemon=True
            )
            self.story_upload_server_thread.start()
            self.story_upload_server_running = True

    def handle_play_video(self, payload: dict) -> dict:
        """
        Handle PLAY_VIDEO request.

        Args:
            payload: Request payload with video_title

        Returns:
            Response dictionary
        """
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
        """Start stories display server."""
        try:
            thread = threading.Thread(
                target=run_stories_display_server,
                daemon=True
            )
            thread.start()

            return self._create_success_response(MESSAGE_STORIES_DISPLAYED)

        except Exception as e:
            return self._create_error_response(str(e))

    def get_videos_display_data(self) -> dict:
        """Start video grid display server."""
        try:
            if run_videos_display_server is None:
                return self._create_error_response(
                    MESSAGE_VIDEO_DISPLAY_UNAVAILABLE
                )

            thread = threading.Thread(
                target=run_videos_display_server,
                daemon=True
            )
            thread.start()

            return self._create_success_response(MESSAGE_VIDEOS_DISPLAYED)

        except Exception as e:
            return self._create_error_response(str(e))

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

    def handle_client(self, client_socket: socket.socket):
        """
        Handle client connection.
        REFACTORED: Split into helper methods.

        Args:
            client_socket: Client socket connection
        """
        try:
            while True:
                request_data = self._receive_request(client_socket)
                if not request_data:
                    break

                response = self._route_request(request_data)
                self._send_response(client_socket, response)

        except Exception as e:
            print(f"[ERROR] Client handling: {e}")
            self._send_error_response(client_socket, str(e))

        finally:
            client_socket.close()

    def _receive_request(self, client_socket: socket.socket) -> dict:
        """
        Receive and parse client request.

        Args:
            client_socket: Client socket

        Returns:
            Parsed request dictionary or None
        """
        data_raw = Protocol.recv(client_socket)
        if not data_raw:
            return None

        # Find JSON start
        start_index = data_raw.find(JSON_START_CHAR)
        if start_index == NOT_FOUND_INDEX:
            raise ValueError("Invalid JSON received")

        # Parse JSON
        data_json = data_raw[start_index:].strip()
        return json.loads(data_json)

    def _route_request(self, request_data: dict) -> dict:
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

        # Unknown
        return self._create_error_response(MESSAGE_UNKNOWN_REQUEST)

    def _send_response(self, client_socket: socket.socket, response: dict):
        """
        Send response to client.

        Args:
            client_socket: Client socket
            response: Response dictionary
        """
        Protocol.send(client_socket, json.dumps(response))

    def _send_error_response(self, client_socket: socket.socket, error: str):
        """
        Send error response to client.

        Args:
            client_socket: Client socket
            error: Error message
        """
        try:
            Protocol.send(
                client_socket,
                json.dumps(self._create_error_response(error))
            )
        except:
            pass

    def _create_error_response(self, message: str) -> dict:
        """Create error response."""
        return {KEY_STATUS: STATUS_ERROR, KEY_MESSAGE: message}

    def _create_success_response(self, message: str) -> dict:
        """Create success response."""
        return {KEY_STATUS: STATUS_SUCCESS, KEY_MESSAGE: message}

if __name__ == '__main__':
    server_app = Server()
    server_app.start()
