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
from handle_show_all_stories import run as run_stories_display_server

# Import for video grid display
try:
    from handle_show_all_videos import run as run_videos_display_server
except ImportError:
    run_videos_display_server = None

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

    # ----------------------------
    # Start the main TCP server
    # ----------------------------
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True

        print("="*50)
        print("🎾 Tennis Social Server")
        print("="*50)
        print(f"Main Server: {self.host}:{self.port}")
        print(f"Story Upload: {self.host}:3333")
        print("="*50)
        print("Server is ready and waiting for clients...")
        print("="*50)

        # Start the story upload server in background (always running)
        self.start_story_upload_server()

        try:
            while self.running:
                client_socket, addr = self.server_socket.accept()

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
        print("\nServer stopped.")

    # -----------------------------------
    # STORY UPLOAD SERVER (Port 3333)
    # -----------------------------------
    def start_story_upload_server(self):
        """Start the story media upload server (runs on port 3333)"""
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

            return {"status": "success", "message": "Story stream started"}

        except Exception as e:
            return {"status": "error", "message": f"Failed to start story server: {e}"}

    # -----------------------------------
    # STORY LIST / WX DISPLAY TRIGGER
    # -----------------------------------
    def get_stories_display_data(self):
        try:
            thread = threading.Thread(target=run_stories_display_server, daemon=True)
            thread.start()

            return {"status": "success", "message": "All stories displayed"}

        except Exception as e:
            return {"status": "error", "message": f"Failed: {e}"}

    # -----------------------------------
    # VIDEO LIST / WX DISPLAY TRIGGER
    # -----------------------------------
    def get_videos_display_data(self):
        """Start the video thumbnail server for grid display"""
        try:
            if run_videos_display_server is None:
                return {"status": "error", "message": "Video display server not available"}

            thread = threading.Thread(target=run_videos_display_server, daemon=True)
            thread.start()

            return {"status": "success", "message": "Video grid display server started"}

        except Exception as e:
            return {"status": "error", "message": f"Failed to start video display: {e}"}

    # -----------------------------------
    # ADD_STORY HANDLER
    # -----------------------------------
    def handle_add_story(self, payload):
        """
        Handle ADD_STORY request.
        Ensures upload server is running before story upload.
        """
        # Make sure upload server is running
        if not self.story_upload_server_running:
            self.start_story_upload_server()
            time.sleep(1)  # Give server time to start

        # Process the story metadata
        response = self.stories_handler.handle_request('ADD_STORY', payload)

        return response

    # -----------------------------------
    # MAIN REQUEST ROUTING
    # -----------------------------------
    def handle_client(self, client_socket):
        try:
            while True:
                data_raw = Protocol.recv(client_socket)
                if not data_raw:
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
                elif request_type == 'ADD_STORY':
                    # Special handler that ensures upload server is running
                    response = self.handle_add_story(payload)

                elif request_type == 'GET_STORIES':
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
                # PLAY STORY – WX STREAMING VERSION
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
                # PLAY STORY – OLD PLAYER
                # ------------------------
                elif request_type == 'PLAY_STORY':
                    response = self.handle_play_story(payload)

                # ------------------------
                # WX "SHOW ALL STORIES"
                # ------------------------
                elif request_type == 'GET_IMAGES_OF_ALL_VIDEOS':
                    response = self.get_stories_display_data()

                # ------------------------
                # WX "SHOW ALL VIDEOS IN GRID"
                # ------------------------
                elif request_type == 'GET_ALL_VIDEOS_GRID':
                    response = self.get_videos_display_data()

                # ------------------------
                # SEND RESPONSE
                # ------------------------
                Protocol.send(client_socket, json.dumps(response))

        except Exception as e:
            print(f"[ERROR] Client handling: {e}")
            try:
                Protocol.send(
                    client_socket,
                    json.dumps({"status": "error", "message": str(e)})
                )
            except:
                pass

        finally:
            client_socket.close()


if __name__ == '__main__':
    server_app = Server()
    server_app.start()