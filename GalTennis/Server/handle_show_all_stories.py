import socket
import json
import os
import cv2
import base64
from pathlib import Path


class VideoServer:
    def __init__(self, video_folder="videos", port=2222):
        self.video_folder = video_folder
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', self.port))

    def extract_thumbnail(self, video_path):
        """Extract a preview thumbnail from the video"""
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()

        if ret:
            # Save the image as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            # Convert to base64
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            return img_base64
        return None

    def get_videos_data(self):
        """Collect all video information"""
        videos_data = []

        if not os.path.exists(self.video_folder):
            os.makedirs(self.video_folder)
            return videos_data

        for file in os.listdir(self.video_folder):
            if file.endswith(('.mp4', '.avi', '.mkv', '.mov')):
                video_path = os.path.join(self.video_folder, file)
                thumbnail = self.extract_thumbnail(video_path)

                if thumbnail:
                    videos_data.append({
                        'name': file,
                        'path': video_path,
                        'thumbnail': thumbnail
                    })

        return videos_data

    def start(self):
        """Start listening for client requests"""
        self.sock.listen(5)
        print(f"Server listening on port {self.port}")

        while True:
            client, address = self.sock.accept()
            print(f"Client connected: {address}")

            try:
                # Receive request from client
                request = client.recv(1024).decode('utf-8')

                if request == "GET_VIDEOS":
                    # Collect information about all videos
                    videos_data = self.get_videos_data()

                    # Send response in JSON format
                    response = json.dumps(videos_data, ensure_ascii=False)
                    client.sendall(response.encode('utf-8'))

                    print(f"Sent {len(videos_data)} videos to client")

            except Exception as e:
                print(f"Error: {e}")
            finally:
                client.close()


def run():
    server = VideoServer()
    server.start()