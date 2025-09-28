import socket
import json
import threading
import sqlite3
import os
from Authication import Authentication
from Videos_Handler import VideosHandler
from Likes_Handler import LikesHandler
from Comments_Handler import CommentsHandler
from Stories_Handler import StoriesHandler
from Manger_commands import ManagerCommands

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 5000
DB_FILE = 'users.db'


class Server:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.running = False

        # Initialize the Handler classes
        self.auth_handler = Authentication()
        self.videos_handler = VideosHandler()
        self.likes_handler = LikesHandler()
        self.comments_handler = CommentsHandler()
        self.stories_handler = StoriesHandler()
        self.manager_commands = ManagerCommands()

        print("Server Handlers Initialized.")

    def start(self):
        """Starts the server and listens for client connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Using SO_REUSEADDR allows the port to be reused immediately after closing
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"✅ Server is running on {self.host}:{self.port}. Awaiting connections...")

        try:
            while self.running:
                client_socket, addr = self.server_socket.accept()
                print(f"Connection established with {addr}")
                # Handle each client in a separate Thread
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
        print("🛑 Server shutdown.")

    def handle_client(self, client_socket):
        """
        Receives data from the client, routes it to the appropriate Handler, and sends a response.
        """
        try:
            # Receive raw data
            data_raw = client_socket.recv(4096).decode('utf-8')

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

            # --- Routing to New Handlers ---
            elif request_type in ['ADD_COMMENT', 'GET_COMMENTS']:
                response = self.comments_handler.handle_request(request_type, payload)

            elif request_type in ['ADD_STORY', 'GET_STORIES']:
                response = self.stories_handler.handle_request(request_type, payload)

            elif request_type in ['GET_ALL_USERS']:  # Manager command
                # Note: Permission check (is_admin) should be performed before executing this command in real use
                response = self.manager_commands.handle_request(request_type, payload)

            # --- Sending Response to Client ---
            client_socket.sendall(json.dumps(response).encode('utf-8'))

        except json.JSONDecodeError:
            print("Received non-JSON data from client.")
            client_socket.sendall(json.dumps({"status": "error", "message": "Invalid request format."}).encode('utf-8'))
        except Exception as e:
            print(f"Error handling client: {e}")
            client_socket.sendall(
                json.dumps({"status": "error", "message": f"Server processing error: {e}"}).encode('utf-8'))
        finally:
            client_socket.close()


if __name__ == '__main__':
    server_app = Server()
    server_app.start()
