import socket
import json
import os
import cv2
import base64
from pathlib import Path


class VideoMediaServer:
    def __init__(self, media_folder="videos", port=2223):
        self.media_folder = media_folder
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', self.port))

        # Supported video extensions
        self.video_extensions = ('.mp4', '.avi', '.mkv', '.mov')

    def extract_thumbnail(self, file_path):
        """Extract first frame as thumbnail from video"""
        try:
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            cap.release()

            if ret:
                # Resize to maximum 200x200
                height, width = frame.shape[:2]
                max_size = 200

                if height > width:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                else:
                    new_width = max_size
                    new_height = int(height * (max_size / width))

                frame = cv2.resize(frame, (new_width, new_height))
                _, buffer = cv2.imencode('.jpg', frame)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                return img_base64
        except Exception as e:
            print(f"Error extracting thumbnail from {file_path}: {e}")

        return None

    def get_video_metadata(self, filename):
        """Extract metadata from database or filename"""
        # This should query the database for video metadata
        # For now, we'll parse from filename or use defaults
        parts = filename.replace('.mp4', '').replace('.avi', '').replace('.mov', '').split('_')

        metadata = {
            'category': 'general',
            'level': 'medium',
            'uploader': 'unknown'
        }

        # Try to extract from filename pattern: category_level_number.mp4
        if len(parts) >= 2:
            metadata['category'] = parts[0] if parts[0] in ['forehand', 'backhand', 'serve', 'slice', 'volley',
                                                            'smash'] else 'general'
            metadata['level'] = parts[1] if parts[1] in ['easy', 'medium', 'hard'] else 'medium'

        # Try to get from database
        try:
            import sqlite3
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT category, difficulty, uploader FROM videos WHERE filename=?",
                (filename,)
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                metadata['category'] = result[0]
                metadata['level'] = result[1]
                metadata['uploader'] = result[2]
        except Exception as e:
            print(f"Error getting metadata from database: {e}")

        return metadata

    def get_videos_data(self):
        """Collect all video file information"""
        media_data = []

        if not os.path.exists(self.media_folder):
            os.makedirs(self.media_folder)
            return media_data

        for file in os.listdir(self.media_folder):
            file_lower = file.lower()
            file_path = os.path.join(self.media_folder, file)

            # Check if it's a video
            if file_lower.endswith(self.video_extensions):
                thumbnail = self.extract_thumbnail(file_path)
                if thumbnail:
                    metadata = self.get_video_metadata(file)
                    media_data.append({
                        'name': file,
                        'path': file_path,
                        'thumbnail': thumbnail,
                        'type': 'video',
                        'category': metadata['category'],
                        'level': metadata['level'],
                        'uploader': metadata['uploader']
                    })

        return media_data

    def start(self):
        """Start listening for client requests"""
        self.sock.listen(5)
        print(f"Video Media Server listening on port {self.port}")
        print(f"Videos folder: {os.path.abspath(self.media_folder)}")

        while True:
            client, address = self.sock.accept()
            print(f"Client connected: {address}")

            try:
                # Receive request from client
                request = client.recv(1024).decode('utf-8')

                if request == "GET_VIDEOS_MEDIA":
                    # Collect information about all video files
                    media_data = self.get_videos_data()

                    # Send response in JSON format
                    response = json.dumps(media_data, ensure_ascii=False)
                    client.sendall(response.encode('utf-8'))

                    videos_count = len(media_data)
                    print(f"Sent {videos_count} videos to client")

            except Exception as e:
                print(f"Error: {e}")
            finally:
                client.close()


def run():
    server = VideoMediaServer()
    server.start()


if __name__ == '__main__':
    run()
