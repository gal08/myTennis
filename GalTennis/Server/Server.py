"""
Gal Haham
Main Tennis Social server application.
Routes client requests, manages handlers, and coordinates
video/story streaming servers.
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
from handle_show_all_stories import run

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 5000
DB_FILE = 'users.db'
VIDEO_FOLDER = "videos"
STORY_FOLDER = "stories"
PREVIEW_LENGTH = 200
NOT_FOUND_INDEX = -1
STARTUP_DELAY_SECONDS = 1
GET_VIDEOS_PHOTOS = 5


class Server:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.running = False
        self.video_server_thread = None
        self.story_server_thread = None

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

        print("Server Handlers Initialized.")

    # ----------------------------
    # Start the main TCP server
    # ----------------------------
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True

        print(f"Server running on {self.host}:{self.port}, waiting for clients...")

        try:
            while self.running:
                client_socket, addr = self.server_socket.accept()
                print(f"Connection established with {addr}")

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,),
                    daemon=True
                )
                client_thread.start()

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"Server error: {e}")
            self.stop()

    def stop(self):
        self.running = False
        self.server_socket.close()
        print("Server stopped.")

    # -----------------------------------
    # PLAY_VIDEO (Used by Video menu)
    # -----------------------------------
    def handle_play_video(self, payload):
        video_title = payload.get('video_title')

        if not video_title:
            return {"status": "error", "message": "Video title not provided"}

        video_path = os.path.join(VIDEO_FOLDER, video_title)

        if not os.path.exists(video_path):
            return {"status": "error", "message": f"Video not found: {video_title}"}

        try:
            thread = threading.Thread(
                target=run_video_player_server,
                args=(video_path,),
                daemon=True
            )
            thread.start()

            print(f"Video streaming server started for: {video_title}")
            return {"status": "success", "message": "Video stream started"}

        except Exception as e:
            return {"status": "error", "message": f"Failed to start video server: {e}"}

    # -----------------------------------
    # PLAY_STORY (old mechanism)
    # -----------------------------------
    def handle_play_story(self, payload):
        story_filename = payload.get('filename')

        if not story_filename:
            return {"status": "error", "message": "Story filename not provided"}

        story_path = os.path.join(STORY_FOLDER, story_filename)

        if not os.path.exists(story_path):
            return {"status": "error", "message": f"Story not found: {story_filename}"}

        try:
            thread = threading.Thread(
                target=run_story_player_server,
                args=(story_filename,),
                daemon=True
            )
            thread.start()

            print(f"Story streaming server started for: {story_filename}")
            return {"status": "success", "message": "Story stream started"}

        except Exception as e:
            return {"status": "error", "message": f"Failed to start story server: {e}"}

    # -----------------------------------
    # STORY LIST / WX DISPLAY TRIGGER
    # -----------------------------------
    def get_videos_data(self):
        try:
            thread = threading.Thread(target=run, daemon=True)
            thread.start()

            return {"status": "success", "message": "All stories displayed"}

        except Exception as e:
            return {"status": "error", "message": f"Failed: {e}"}

    # -----------------------------------
    # MAIN REQUEST ROUTING
    # -----------------------------------
    def handle_client(self, client_socket):
        try:
            print("Client connected")

            while True:
                data_raw = Protocol.recv(client_socket)
                if not data_raw:
                    print("Client disconnected")
                    break

                start_index = data_raw.find('{')
                if start_index == NOT_FOUND_INDEX:
                    raise ValueError("Invalid JSON received")

                data_json = data_raw[start_index:].strip()
                request_data = json.loads(data_json)

                request_type = request_data.get('type')
                payload = request_data.get('payload', {})

                response = {"status": "error", "message": "Unknown request"}

                # ------------------------
                # Authentication
                # ------------------------
                if request_type in ['LOGIN', 'SIGNUP']:
                    response = self.auth_handler.handle_request(request_type, payload)

                # ------------------------
                # Videos
                # ------------------------
                elif request_type in ['ADD_VIDEO', 'GET_VIDEOS']:
                    response = self.videos_handler.handle_request(request_type, payload)

                # ------------------------
                # Likes
                # ------------------------
                elif request_type in ['LIKE_VIDEO', 'GET_LIKES_COUNT']:
                    response = self.likes_handler.handle_request(request_type, payload)

                # ------------------------
                # Comments
                # ------------------------
                elif request_type in ['ADD_COMMENT', 'GET_COMMENTS']:
                    response = self.comments_handler.handle_request(request_type, payload)

                # ------------------------
                # Stories DB ops
                # ------------------------
                elif request_type in ['ADD_STORY', 'GET_STORIES']:
                    response = self.stories_handler.handle_request(request_type, payload)

                # ------------------------
                # Manager Commands
                # ------------------------
                elif request_type == 'GET_ALL_USERS':
                    response = self.manager_commands.handle_request(request_type, payload)

                # ------------------------
                # PLAY VIDEO
                # ------------------------
                elif request_type == 'PLAY_VIDEO':
                    response = self.handle_play_video(payload)

                # ------------------------
                # PLAY STORY — WX STREAMING VERSION
                # ------------------------
                elif request_type == 'PLAY_STORY_MEDIA':
                    filename = payload.get("filename")
                    story_path = os.path.join(STORY_FOLDER, filename)

                    if not os.path.exists(story_path):
                        response = {
                            "status": "error",
                            "message": f"Story file not found: {filename}"
                        }
                    else:
                        from VideoAudioServer import VideoAudioServer

                        def start_stream_story():
                            server = VideoAudioServer(
                                story_path,
                                host="0.0.0.0",
                                port=9999
                            )
                            server.start()

                        threading.Thread(
                            target=start_stream_story,
                            daemon=True
                        ).start()

                        response = {
                            "status": "success",
                            "message": "Story streaming started"
                        }

                # ------------------------
                # PLAY STORY — OLD PLAYER
                # ------------------------
                elif request_type == 'PLAY_STORY':
                    response = self.handle_play_story(payload)

                # ------------------------
                # WX "SHOW ALL STORIES"
                # ------------------------
                elif request_type == 'GET_IMAGES_OF_ALL_VIDEOS':
                    response = self.get_videos_data()

                # ------------------------
                # SEND RESPONSE
                # ------------------------
                Protocol.send(client_socket, json.dumps(response))
                print(f"[DEBUG] Response sent: {response.get('status')}")

        except Exception as e:
            print(f"Error handling client: {e}")
            try:
                Protocol.send(
                    client_socket,
                    json.dumps({"status": "error", "message": str(e)})
                )
            except:
                pass

        finally:
            client_socket.close()
            print("Client socket closed.")


if __name__ == '__main__':
    server_app = Server()
    server_app.start()
