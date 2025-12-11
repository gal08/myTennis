import socket
import json
import os
import cv2
import base64
from pathlib import Path


class MediaServer:
    def __init__(self, media_folder="stories", port=2222):
        self.media_folder = media_folder
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', self.port))

        # Supported file extensions
        self.video_extensions = ('.mp4', '.avi', '.mkv', '.mov')
        self.image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

    def extract_thumbnail(self, file_path, file_type):
        """Extract preview thumbnail"""
        if file_type == 'image':
            # For images - simply read the image
            img = cv2.imread(file_path)
            if img is not None:
                # Resize image to maximum 200x200
                height, width = img.shape[:2]
                max_size = 200

                if height > width:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                else:
                    new_width = max_size
                    new_height = int(height * (max_size / width))

                img = cv2.resize(img, (new_width, new_height))
                _, buffer = cv2.imencode('.jpg', img)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                return img_base64

        elif file_type == 'video':
            # For videos - extract first frame
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            cap.release()

            if ret:
                _, buffer = cv2.imencode('.jpg', frame)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                return img_base64

        return None

    def get_media_data(self):
        """Collect all media file information"""
        media_data = []

        if not os.path.exists(self.media_folder):
            os.makedirs(self.media_folder)
            return media_data

        for file in os.listdir(self.media_folder):
            file_lower = file.lower()
            file_path = os.path.join(self.media_folder, file)

            # Check if it's a video
            if file_lower.endswith(self.video_extensions):
                thumbnail = self.extract_thumbnail(file_path, 'video')
                if thumbnail:
                    media_data.append({
                        'name': file,
                        'path': file_path,
                        'thumbnail': thumbnail,
                        'type': 'video'
                    })

            # Check if it's an image
            elif file_lower.endswith(self.image_extensions):
                thumbnail = self.extract_thumbnail(file_path, 'image')
                if thumbnail:
                    media_data.append({
                        'name': file,
                        'path': file_path,
                        'thumbnail': thumbnail,
                        'type': 'image'
                    })

        return media_data

    def start(self):
        """Start listening for client requests"""
        self.sock.listen(5)
        print(f"Server listening on port {self.port}")
        print(f"Media folder: {os.path.abspath(self.media_folder)}")

        while True:
            client, address = self.sock.accept()
            print(f"Client connected: {address}")

            try:
                # Receive request from client
                request = client.recv(1024).decode('utf-8')

                if request == "GET_MEDIA":
                    # Collect information about all media files
                    media_data = self.get_media_data()

                    # Send response in JSON format
                    response = json.dumps(media_data, ensure_ascii=False)
                    client.sendall(response.encode('utf-8'))

                    videos_count = sum(1 for m in media_data if m['type'] == 'video')
                    images_count = sum(1 for m in media_data if m['type'] == 'image')
                    print(f"Sent {videos_count} videos and {images_count} images to client")

            except Exception as e:
                print(f"Error: {e}")
            finally:
                client.close()


def run():
    server = MediaServer()
    server.start()
