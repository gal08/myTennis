"""
Gal Haham
Video media server for displaying video thumbnails with metadata.
Handles video preview generation, metadata extraction,
 and streaming to clients.
"""
import socket
import json
import os
import cv2
import base64
import sqlite3
from pathlib import Path


DEFAULT_MEDIA_FOLDER = "videos"
DEFAULT_PORT = 2223
DEFAULT_HOST = "0.0.0.0"
MAX_PENDING_CONNECTIONS = 5
RECEIVE_BUFFER_SIZE = 1024

DATABASE_NAME = 'users.db'
DATABASE_QUERY_VIDEOS = (
    "SELECT category, difficulty, uploader "
    "FROM videos "
    "WHERE filename=?"
)

VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mkv', '.mov')
EXTENSION_MP4 = '.mp4'
EXTENSION_AVI = '.avi'
EXTENSION_MOV = '.mov'

THUMBNAIL_MAX_SIZE = 200
IMAGE_SHAPE_SLICE_2D = 2

ENCODING_FORMAT = 'utf-8'
JPEG_EXTENSION = '.jpg'
ENSURE_ASCII_DISABLED = False

MEDIA_TYPE_VIDEO = 'video'

REQUEST_GET_VIDEOS_MEDIA = "GET_VIDEOS_MEDIA"

CATEGORY_FOREHAND = 'forehand'
CATEGORY_BACKHAND = 'backhand'
CATEGORY_SERVE = 'serve'
CATEGORY_SLICE = 'slice'
CATEGORY_VOLLEY = 'volley'
CATEGORY_SMASH = 'smash'
CATEGORY_GENERAL = 'general'

VALID_CATEGORIES = [
    CATEGORY_FOREHAND,
    CATEGORY_BACKHAND,
    CATEGORY_SERVE,
    CATEGORY_SLICE,
    CATEGORY_VOLLEY,
    CATEGORY_SMASH
]

LEVEL_EASY = 'easy'
LEVEL_MEDIUM = 'medium'
LEVEL_HARD = 'hard'

VALID_LEVELS = [LEVEL_EASY, LEVEL_MEDIUM, LEVEL_HARD]

DEFAULT_CATEGORY = CATEGORY_GENERAL
DEFAULT_LEVEL = LEVEL_MEDIUM
DEFAULT_UPLOADER = 'unknown'

KEY_CATEGORY = 'category'
KEY_LEVEL = 'level'
KEY_UPLOADER = 'uploader'
KEY_NAME = 'name'
KEY_PATH = 'path'
KEY_THUMBNAIL = 'thumbnail'
KEY_TYPE = 'type'

DB_RESULT_CATEGORY = 0
DB_RESULT_LEVEL = 1
DB_RESULT_UPLOADER = 2

FILENAME_SPLIT_CHAR = '_'
MIN_FILENAME_PARTS = 2
FILENAME_CATEGORY_INDEX = 0
FILENAME_LEVEL_INDEX = 1


class VideoMediaServer:
    """
    Video media server that provides thumbnail previews with metadata.

    Responsibilities:
    - Listen for client connections
    - Scan video folder and extract metadata
    - Generate thumbnails for preview
    - Query database for video information
    - Send video information to clients
    """

    def __init__(
            self,
            media_folder: str = DEFAULT_MEDIA_FOLDER,
            port: int = DEFAULT_PORT
    ):
        """
        Initialize the video media server.

        Args:
            media_folder: Directory containing video files
            port: Port to listen on
        """
        self.media_folder = media_folder
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((DEFAULT_HOST, self.port))

        # Supported video extensions
        self.video_extensions = VIDEO_EXTENSIONS

    def extract_thumbnail(self, file_path: str):
        """
        Extract first frame as thumbnail from video.
        REFACTORED: Split into helper methods.

        Args:
            file_path: Path to video file

        Returns:
            Base64 encoded thumbnail or None if extraction failed
        """
        try:
            frame = self._read_first_frame(file_path)
            if frame is None:
                return None

            resized_frame = self._resize_to_thumbnail(frame)
            return self._encode_frame_to_base64(resized_frame)

        except Exception as e:
            print(f"Error extracting thumbnail from {file_path}: {e}")
            return None

    def _read_first_frame(self, file_path: str):
        """
        Read the first frame from a video file.

        Args:
            file_path: Path to video file

        Returns:
            Frame array or None if read failed
        """
        cap = cv2.VideoCapture(file_path)
        ret, frame = cap.read()
        cap.release()

        return frame if ret else None

    def _resize_to_thumbnail(self, frame):
        """
        Resize frame to thumbnail size while maintaining aspect ratio.

        Args:
            frame: OpenCV frame array

        Returns:
            Resized frame
        """
        height, width = frame.shape[:IMAGE_SHAPE_SLICE_2D]

        # Calculate new dimensions
        if height > width:
            new_height = THUMBNAIL_MAX_SIZE
            new_width = int(width * (THUMBNAIL_MAX_SIZE / height))
        else:
            new_width = THUMBNAIL_MAX_SIZE
            new_height = int(height * (THUMBNAIL_MAX_SIZE / width))

        return cv2.resize(frame, (new_width, new_height))

    def _encode_frame_to_base64(self, frame) -> str:
        """
        Encode frame to base64 string.

        Args:
            frame: OpenCV frame array

        Returns:
            Base64 encoded string
        """
        _, buffer = cv2.imencode(JPEG_EXTENSION, frame)
        return base64.b64encode(buffer).decode(ENCODING_FORMAT)

    def get_video_metadata(self, filename: str) -> dict:
        """
        Extract metadata from database or filename.
        REFACTORED: Split into helper methods.

        Args:
            filename: Video filename

        Returns:
            Dictionary with category, level, and uploader
        """
        # Start with defaults
        metadata = self._create_default_metadata()

        # Try to parse from filename
        self._parse_metadata_from_filename(filename, metadata)

        # Try to get from database (overrides filename parsing)
        self._fetch_metadata_from_database(filename, metadata)

        return metadata

    def _create_default_metadata(self) -> dict:
        """
        Create metadata dictionary with default values.

        Returns:
            Dictionary with default metadata
        """
        return {
            KEY_CATEGORY: DEFAULT_CATEGORY,
            KEY_LEVEL: DEFAULT_LEVEL,
            KEY_UPLOADER: DEFAULT_UPLOADER
        }

    def _parse_metadata_from_filename(self, filename: str, metadata: dict):
        """
        Parse metadata from filename pattern: category_level_number.mp4

        Args:
            filename: Video filename
            metadata: Dictionary to update with parsed values
        """
        # Remove extensions
        clean_name = filename
        for ext in [EXTENSION_MP4, EXTENSION_AVI, EXTENSION_MOV]:
            clean_name = clean_name.replace(ext, '')

        # Split by underscore
        parts = clean_name.split(FILENAME_SPLIT_CHAR)

        # Parse if enough parts
        if len(parts) >= MIN_FILENAME_PARTS:
            category = parts[FILENAME_CATEGORY_INDEX]
            level = parts[FILENAME_LEVEL_INDEX]

            # Validate and set category
            if category in VALID_CATEGORIES:
                metadata[KEY_CATEGORY] = category

            # Validate and set level
            if level in VALID_LEVELS:
                metadata[KEY_LEVEL] = level

    def _fetch_metadata_from_database(self, filename: str, metadata: dict):
        """
        Fetch metadata from database and update dictionary.

        Args:
            filename: Video filename
            metadata: Dictionary to update with database values
        """
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute(DATABASE_QUERY_VIDEOS, (filename,))
            result = cursor.fetchone()
            conn.close()

            if result:
                metadata[KEY_CATEGORY] = result[DB_RESULT_CATEGORY]
                metadata[KEY_LEVEL] = result[DB_RESULT_LEVEL]
                metadata[KEY_UPLOADER] = result[DB_RESULT_UPLOADER]

        except Exception as e:
            print(f"Error getting metadata from database: {e}")

    def get_videos_data(self) -> list:
        """
        Collect information about all video files in folder.

        Returns:
            List of dictionaries with video information
        """
        media_data = []

        # Ensure folder exists
        if not self._ensure_videos_folder_exists():
            return media_data

        # Scan folder for video files
        for file in os.listdir(self.media_folder):
            if self._is_video_file(file):
                video_info = self._create_video_info(file)
                if video_info:
                    media_data.append(video_info)

        return media_data

    def _ensure_videos_folder_exists(self) -> bool:
        """
        Ensure videos folder exists, create if needed.

        Returns:
            bool: True if folder exists or was created
        """
        if not os.path.exists(self.media_folder):
            os.makedirs(self.media_folder)
            return False
        return True

    def _is_video_file(self, filename: str) -> bool:
        """
        Check if file is a supported video format.

        Args:
            filename: Filename to check

        Returns:
            bool: True if file is a video
        """
        return filename.lower().endswith(self.video_extensions)

    def _create_video_info(self, filename: str):
        """
        Create video information dictionary.

        Args:
            filename: Video filename

        Returns:
            Dictionary with video info or None if thumbnail extraction failed
        """
        file_path = os.path.join(self.media_folder, filename)
        thumbnail = self.extract_thumbnail(file_path)

        if not thumbnail:
            return None

        metadata = self.get_video_metadata(filename)

        return {
            KEY_NAME: filename,
            KEY_PATH: file_path,
            KEY_THUMBNAIL: thumbnail,
            KEY_TYPE: MEDIA_TYPE_VIDEO,
            KEY_CATEGORY: metadata[KEY_CATEGORY],
            KEY_LEVEL: metadata[KEY_LEVEL],
            KEY_UPLOADER: metadata[KEY_UPLOADER]
        }

    def start(self):
        """
        Start listening for client requests.
        Runs continuously until stopped.
        REFACTORED: Split client handling into separate method.
        """
        self.sock.listen(MAX_PENDING_CONNECTIONS)
        print(f"Video Media Server listening on port {self.port}")
        print(f"Videos folder: {os.path.abspath(self.media_folder)}")

        while True:
            client, address = self.sock.accept()
            print(f"Client connected: {address}")

            try:
                self._handle_client_request(client)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                client.close()

    def _handle_client_request(self, client: socket.socket):
        """
        Handle a single client request.

        Args:
            client: Client socket connection
        """
        # Receive request
        request = client.recv(RECEIVE_BUFFER_SIZE).decode(ENCODING_FORMAT)

        # Process request
        if request == REQUEST_GET_VIDEOS_MEDIA:
            self._send_videos_list(client)

    def _send_videos_list(self, client: socket.socket):
        """
        Send list of video files to client.

        Args:
            client: Client socket connection
        """
        # Collect video data
        media_data = self.get_videos_data()

        # Send response
        response = json.dumps(media_data, ensure_ascii=ENSURE_ASCII_DISABLED)
        client.sendall(response.encode(ENCODING_FORMAT))

        # Log statistics
        videos_count = len(media_data)
        print(f"Sent {videos_count} videos to client")


def run():
    """
    Entry point for starting the video media server.

    Creates a VideoMediaServer instance with default settings and starts it.
    """
    server = VideoMediaServer()
    server.start()


if __name__ == '__main__':
    run()
