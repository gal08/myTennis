"""
Gal Haham
Main Tennis Social server application.
Routes client requests, manages handlers, and coordinates
video/story streaming servers.
"""
import socket
import json
import threading
import os
import time

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

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 5000
DB_FILE = 'users.db'
VIDEO_FOLDER = "videos"
STORY_FOLDER = "stories"
PREVIEW_LENGTH = 200
NOT_FOUND_INDEX = -1
STARTUP_DELAY_SECONDS = 1


class Server:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.running = False
        self.video_server_thread = None
        self.story_server_thread = None

        # Initialize the Handler classes
        self.auth_handler = Authentication()
        self.videos_handler = VideosHandler()
        self.likes_handler = LikesHandler()
        self.comments_handler = CommentsHandler()
        self.stories_handler = StoriesHandler()
        self.manager_commands = ManagerCommands()

        # Ensure video folder exists
        if not os.path.exists(VIDEO_FOLDER):
            os.makedirs(VIDEO_FOLDER)

        # Ensure story folder exists
        if not os.path.exists(STORY_FOLDER):
            os.makedirs(STORY_FOLDER)

        print("Server Handlers Initialized.")

    def start(self):
        """Starts the server and listens for client connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(
            f"Server is running on {self.host}:{self.port}. "
            "Awaiting connections..."
        )

        try:
            while self.running:
                client_socket, addr = self.server_socket.accept()
                print(f"Connection established with {addr}")
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )

                client_thread.start()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"Server error: {e}")
            self.stop()

    def stop(self):
        """Stops the server."""
        self.running = False
        self.server_socket.close()
        print("Server shutdown.")

    def handle_play_video(self, payload):
        """Handles PLAY_VIDEO request by
        starting the video streaming server."""
        video_title = payload.get('video_title')

        if not video_title:
            return {"status": "error", "message": "Video title not provided"}

        video_path = os.path.join(VIDEO_FOLDER, video_title)

        # Check if video file exists
        if not os.path.exists(video_path):
            return {
                "status": "error",
                "message": f"Video file not found: {video_title}"
            }

        try:
            # Start video streaming server in background thread
            self.video_server_thread = threading.Thread(
                target=run_video_player_server,
                args=(video_path,),
                daemon=True
            )
            self.video_server_thread.start()

            print(f"Video streaming server started for: {video_title}")
            return {
                "status": "success",
                "message": "Video server started. Ready to stream."
            }

        except Exception as e:
            print(f"Error starting video server: {e}")
            return {
                "status": "error",
                "message": f"Failed to start video server: {e}"
            }

    def handle_play_story(self, payload):
        """Handles PLAY_STORY request by starting
        the story streaming server."""
        story_filename = payload.get('filename')

        if not story_filename:
            return {
                "status": "error",
                "message": "Story filename not provided"
            }

        story_path = os.path.join(STORY_FOLDER, story_filename)

        # Check if story file exists
        if not os.path.exists(story_path):
            return {
                "status": "error",
                "message": f"Story file not found: {story_filename}"
            }

        try:
            # Start story streaming server in background thread
            self.story_server_thread = threading.Thread(
                target=run_story_player_server,
                args=(story_filename,),
                daemon=True
            )
            self.story_server_thread.start()

            print(f"Story streaming server started for: {story_filename}")
            return {
                "status": "success",
                "message": "Story server started. Ready to stream."
            }

        except Exception as e:
            print(f"Error starting story server: {e}")
            return {
                "status": "error",
                "message": f"Failed to start story server: {e}"
            }

    def handle_client(self, client_socket):
        """Handle client requests and route to appropriate handlers.
        Manages request-response loop until client disconnects"""
        try:
            print("Client connected")

            while True:
                data_raw = Protocol.recv(client_socket)

                if not data_raw:
                    print("Client disconnected.")
                    break

                start_index = data_raw.find('{')
                if start_index == NOT_FOUND_INDEX:
                    raise ValueError("JSON start character '{' not found.")

                data_raw_json = data_raw[start_index:].strip()
                print(f"[DEBUG] Cleaned JSON data: {data_raw_json[:PREVIEW_LENGTH]}...")

                request_data = json.loads(data_raw_json)
                print(f"[DEBUG] Parsed request_data: {request_data}")

                request_type = request_data.get('type')
                payload = request_data.get('payload', {})

                response = {
                    "status": "error",
                    "message": "Unrecognized request"
                }

                should_start_media_server = False

                # --- Routing ---
                if request_type in ['LOGIN', 'SIGNUP']:
                    response = self.auth_handler.handle_request(
                        request_type,
                        payload
                    )

                elif request_type in ['ADD_VIDEO', 'GET_VIDEOS']:
                    response = self.videos_handler.handle_request(
                        request_type,
                        payload
                    )

                elif request_type in ['LIKE_VIDEO', 'GET_LIKES_COUNT']:
                    response = self.likes_handler.handle_request(
                        request_type,
                        payload
                    )

                elif request_type in ['ADD_COMMENT', 'GET_COMMENTS']:
                    response = self.comments_handler.handle_request(
                        request_type,
                        payload
                    )

                elif request_type in ['ADD_STORY', 'GET_STORIES']:
                    response = self.stories_handler.handle_request(
                        request_type,
                        payload
                    )
                    if (
                            request_type == 'ADD_STORY' and
                            response.get('status') == 'success'
                    ):
                        should_start_media_server = True

                elif request_type in ['GET_ALL_USERS']:
                    response = self.manager_commands.handle_request(
                        request_type,
                        payload
                    )

                elif request_type == 'PLAY_VIDEO':
                    response = self.handle_play_video(payload)

                elif request_type == 'PLAY_STORY':
                    response = self.handle_play_story(payload)

                Protocol.send(client_socket, json.dumps(response))
                print(f"[DEBUG] Response sent: {response.get('status')}")

                if should_start_media_server:
                    def start_media_server():
                        """
                        Start the media server in a separate thread.
                        Waits 1 second before starting to ensure client is ready.
                        """
                        try:
                            print(
                                "Waiting 1 second before starting media..."
                            )
                            time.sleep(STARTUP_DELAY_SECONDS)
                            print("Starting media server...")
                            story_saver_server.run()
                        except Exception as e:
                            print(f"Media server error: {e}")

                    threading.Thread(
                        target=start_media_server,
                        daemon=True
                    ).start()
                    print("[DEBUG] Media server thread started")

        except Exception as e:
            print(f"Error handling client: {e}")
            import traceback
            traceback.print_exc()
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
