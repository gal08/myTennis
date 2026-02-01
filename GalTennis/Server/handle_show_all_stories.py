"""
Gal Haham
Media server for displaying story thumbnails.
Handles image and video preview generation and streaming to clients.
"""
import socket
import json
import os
import cv2
import base64
from pathlib import Path
from Protocol import Protocol
import key_exchange

DEFAULT_MEDIA_FOLDER = "stories"
DEFAULT_PORT = 2222
DEFAULT_HOST = "0.0.0.0"
MAX_PENDING_CONNECTIONS = 5
RECEIVE_BUFFER_SIZE = 1024

VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mkv', '.mov')
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

THUMBNAIL_MAX_SIZE = 200
IMAGE_SHAPE_SLICE_2D = 2

ENCODING_FORMAT = 'utf-8'
JPEG_EXTENSION = '.jpg'
ENSURE_ASCII_DISABLED = False

MEDIA_TYPE_IMAGE = 'image'
MEDIA_TYPE_VIDEO = 'video'

REQUEST_GET_MEDIA = "GET_MEDIA"

COUNT_START = 1


class MediaServer:
    """
    Media server that provides thumbnail previews of stories.

    Responsibilities:
    - Listen for client connections
    - Scan media folder for images and videos
    - Generate thumbnails for preview
    - Send media information to clients
    """

    def __init__(
            self,
            media_folder: str = DEFAULT_MEDIA_FOLDER,
            port: int = DEFAULT_PORT
    ):
        """
        Initialize the media server.

        Args:
            media_folder: Directory containing media files
            port: Port to listen on
        """
        self.media_folder = media_folder
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((DEFAULT_HOST, self.port))
        #temp_conn = (self.sock, None)
        #key = key_exchange.KeyExchange.send_recv_key(temp_conn)
        #self.conn = (self.sock, key)

        # Supported file extensions
        self.video_extensions = VIDEO_EXTENSIONS
        self.image_extensions = IMAGE_EXTENSIONS
        self.conn = (0, 0)

    def extract_thumbnail(self, file_path: str, file_type: str):
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
            return self._extract_image_thumbnail(file_path)
        elif file_type == MEDIA_TYPE_VIDEO:
            return self._extract_video_thumbnail(file_path)
        return None

    def _extract_image_thumbnail(self, file_path: str):
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
        resized_img = self._resize_to_thumbnail(img)

        # Encode to base64
        return self._encode_image_to_base64(resized_img)

    def _extract_video_thumbnail(self, file_path: str):
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

        return self._encode_image_to_base64(frame)

    def _resize_to_thumbnail(self, img):
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

    def _encode_image_to_base64(self, img) -> str:
        """
        Encode image to base64 string.

        Args:
            img: OpenCV image array

        Returns:
            Base64 encoded string
        """
        _, buffer = cv2.imencode(JPEG_EXTENSION, img)
        return base64.b64encode(buffer).decode(ENCODING_FORMAT)

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

        # Ensure folder exists
        if not self._ensure_media_folder_exists():
            return media_data

        # Scan folder for media files
        for file in os.listdir(self.media_folder):
            file_lower = file.lower()
            file_path = os.path.join(self.media_folder, file)

            # Check if it's a video
            if file_lower.endswith(self.video_extensions):
                self._add_video_to_list(media_data, file, file_path)

            # Check if it's an image
            elif file_lower.endswith(self.image_extensions):
                self._add_image_to_list(media_data, file, file_path)

        return media_data

    def _ensure_media_folder_exists(self) -> bool:
        """
        Ensure media folder exists, create if needed.

        Returns:
            bool: True if folder exists or was created
        """
        if not os.path.exists(self.media_folder):
            os.makedirs(self.media_folder)
            return False
        return True

    def _add_video_to_list(
            self,
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
        thumbnail = self.extract_thumbnail(file_path, MEDIA_TYPE_VIDEO)
        if thumbnail:
            media_data.append({
                'name': filename,
                'path': file_path,
                'thumbnail': thumbnail,
                'type': MEDIA_TYPE_VIDEO
            })

    def _add_image_to_list(
            self,
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
        thumbnail = self.extract_thumbnail(file_path, MEDIA_TYPE_IMAGE)
        if thumbnail:
            media_data.append({
                'name': filename,
                'path': file_path,
                'thumbnail': thumbnail,
                'type': MEDIA_TYPE_IMAGE
            })

    def start(self):
        """
        Start listening for client requests.
        Runs continuously until stopped.
        REFACTORED: Split client handling into separate method.
        """
        self.sock.listen(MAX_PENDING_CONNECTIONS)
        print(f"Server listening on port {self.port}")
        print(f"Media folder: {os.path.abspath(self.media_folder)}")

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

        temp_conn = (self.sock, None)
        key = key_exchange.KeyExchange.send_recv_key(temp_conn)
        self.conn = (self.sock, key)
        # Receive request
        response_data = Protocol.recv(self.conn)

        # Process request
        if response_data.get('type') == "GET_MEDIA":
            self._send_media_list(client)

    def _send_media_list(self, client: socket.socket):
        """
        Send list of media files to client.

        Args:
            client: Client socket connection
        """
        # Collect media data
        media_data = self.get_media_data()
        print("iiii")
        print(media_data)
        request_data = json.dumps({
            "type": 'RES_GET_MEDIA',
            "payload": media_data
        })
        Protocol.send(request_data, self.conn)

        # Log statistics
        self._log_media_stats(media_data)

    def _log_media_stats(self, media_data: list):
        """
        Log statistics about sent media.

        Args:
            media_data: List of media items
        """
        videos_count = sum(
            COUNT_START
            for m in media_data
            if m['type'] == MEDIA_TYPE_VIDEO
        )
        images_count = sum(
            COUNT_START
            for m in media_data
            if m['type'] == MEDIA_TYPE_IMAGE
        )
        print(
            f"Sent {videos_count} videos and "
            f"{images_count} images to client"
        )


def run():
    """
    Entry point for starting the media server.

    Creates a MediaServer instance with default settings and starts it.
    """
    server = MediaServer()
    server.start()
