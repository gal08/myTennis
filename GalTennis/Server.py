import socket
import json
import threading
import sqlite3
import os
from Protocol import Protocol
from Authication import Authentication
from Videos_Handler import VideosHandler
from Likes_Handler import LikesHandler
from Comments_Handler import CommentsHandler
from Stories_Handler import StoriesHandler
from Manger_commands import ManagerCommands
from Video_Player_Server import run_video_player_server

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 5000
DB_FILE = 'users.db'
VIDEO_FOLDER = "videos"


class Server:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.running = False
        self.video_server_thread = None

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

        print("Server Handlers Initialized.")

    def start(self):
        """Starts the server and listens for client connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"Server is running on {self.host}:{self.port}. Awaiting connections...")

        try:
            while self.running:
                client_socket, addr = self.server_socket.accept()
                print(f"Connection established with {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
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
        """Handles PLAY_VIDEO request by starting the video streaming server."""
        video_title = payload.get('video_title')
        
        if not video_title:
            return {"status": "error", "message": "Video title not provided"}
        
        video_path = os.path.join(VIDEO_FOLDER, video_title)
        
        # Check if video file exists
        if not os.path.exists(video_path):
            return {"status": "error", "message": f"Video file not found: {video_title}"}
        
        try:
            # Start video streaming server in background thread
            self.video_server_thread = threading.Thread(
                target=run_video_player_server,
                args=(video_path,),
                daemon=True
            )
            self.video_server_thread.start()
            
            print(f"Video streaming server started for: {video_title}")
            return {"status": "success", "message": "Video server started. Ready to stream."}
            
        except Exception as e:
            print(f"Error starting video server: {e}")
            return {"status": "error", "message": f"Failed to start video server: {e}"}

    def handle_client(self, client_socket):
        """
        Receives data from the client using Protocol, routes it to the appropriate Handler,
        and sends a response using Protocol.
        """
        try:
            # Receive data using Protocol.recv()
            data_raw = Protocol.recv(client_socket)

            if not data_raw:
                return

            # Client sends JSON
            request_data = json.loads(data_raw)
            request_type = request_data.get('type')
            payload = request_data.get('payload', {})

            response = {"status": "error", "message": "Unrecognized request"}

            # --- Request Routing ---
            if request_type in ['LOGIN', 'SIGNUP']:
                response = self.auth_handler.handle_request(request_type, payload)

            elif request_type in ['ADD_VIDEO', 'GET_VIDEOS']:
                response = self.videos_handler.handle_request(request_type, payload)

            elif request_type in ['LIKE_VIDEO', 'GET_LIKES_COUNT']:
                response = self.likes_handler.handle_request(request_type, payload)

            elif request_type in ['ADD_COMMENT', 'GET_COMMENTS']:
                response = self.comments_handler.handle_request(request_type, payload)

            elif request_type in ['ADD_STORY', 'GET_STORIES']:
                response = self.stories_handler.handle_request(request_type, payload)

            elif request_type in ['GET_ALL_USERS']:
                response = self.manager_commands.handle_request(request_type, payload)

            elif request_type == 'PLAY_VIDEO':
                response = self.handle_play_video(payload)

            # --- Sending Response to Client using Protocol ---
            Protocol.send(client_socket, json.dumps(response))

        except json.JSONDecodeError:
            print("Received non-JSON data from client.")
            Protocol.send(client_socket, json.dumps({"status": "error", "message": "Invalid request format."}))
        except Exception as e:
            print(f"Error handling client: {e}")
            try:
                Protocol.send(client_socket, json.dumps({"status": "error", "message": f"Server processing error: {e}"}))
            except:
                pass
        finally:
            client_socket.close()


if __name__ == '__main__':
    server_app = Server()
    server_app.start()