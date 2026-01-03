"""
Gal Haham
Main client for Tennis Social application.
Handles server connection and provides backend services for GUI.
Primary entry point for the application.
REFACTORED: Magic numbers replaced with constants, long methods split.
"""
import socket
import json
import os
import sys
import time
import wx
import base64

import Show_all_stories_in_wx
from Protocol import Protocol
from story_player_client import run_story_player_client
from LoginSignupFrame import LoginSignupFrame
from Read_server_ip import readServerIp


# --- Configuration ---
HOST = readServerIp()
PORT = 5000
VIDEO_FOLDER = "videos"
TWO_SECOND_PAUSE = 2
ATTEMPTS_LIMIT = 5
HALF_SECOND_DELAY = 0.5
PATH_LIST_HEAD = 0
EXIT_CODE_ERROR = 1
EXIT_CODE_SUCCESS = 0

# User roles
USER_ROLE_REGULAR = 0
USER_ROLE_ADMIN = 1

# Story file names
STORY_VIDEO_FILENAME = "story.mp4"
STORY_IMAGE_FILENAME = "story.jpg"


class Client:
    """
    Client class for the Tennis Social application.
    Provides backend services for the GUI interface.
    """

    def __init__(self):
        """
        Initialize the Tennis Social client.

        Sets up network configuration, user state, and file system.
        """
        self.host = HOST
        self.port = PORT
        self.username = None
        self.is_admin = USER_ROLE_REGULAR
        self._ensure_video_folder_exists()

    def _ensure_video_folder_exists(self):
        """Create video folder if it doesn't exist."""
        if not os.path.exists(VIDEO_FOLDER):
            os.makedirs(VIDEO_FOLDER)

    def _send_request(self, request_type, payload):
        """
        Sends a JSON request to the server using Protocol
        and returns the server's JSON response.

        Args:
            request_type: Type of request (e.g., 'LOGIN', 'ADD_STORY')
            payload: Dictionary containing request data

        Returns:
            dict: Server response with 'status' and optional data
        """
        try:
            # Create a socket connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))

            # Prepare request data as JSON
            request_data = json.dumps({
                "type": request_type,
                "payload": payload
            })

            # Send data to the server using Protocol
            Protocol.send(client_socket, request_data)

            # Receive the response using Protocol
            response_data = Protocol.recv(client_socket)
            response = json.loads(response_data)

            return response

        except ConnectionRefusedError:
            return {
                "status": "error",
                "message": "Connection Refused. Is server running?",
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid server response format.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Network Error: {e}"}

    def on_story_post_callback(self, caption, media_type, media_data):
        """
        Callback for posting a story from the camera - REFACTORED.
        Called by Story_camera.py after capturing media.

        Args:
            caption: Story caption (currently unused)
            media_type: Type of media ('video' or 'photo')
            media_data: Base64 encoded media data
        """
        # Step 1: Determine filename and save locally
        file_name = self._get_story_filename(media_type)
        if not self._save_story_file(file_name, media_data):
            return

        # Step 2: Register story in database
        if not self._register_story_in_database(file_name, media_type):
            self._cleanup_file(file_name)
            return

        # Step 3: Upload to server and verify
        self._upload_and_verify_story(file_name)

        # Step 4: Cleanup
        self._cleanup_file(file_name)

    def _get_story_filename(self, media_type):
        """
        Get appropriate filename based on media type.

        Args:
            media_type: 'video' or 'photo'

        Returns:
            str: Filename to use
        """
        if media_type == "video":
            return STORY_VIDEO_FILENAME
        else:
            return STORY_IMAGE_FILENAME

    def _save_story_file(self, file_name, media_data):
        """
        Save base64 encoded media to file.

        Args:
            file_name: Name of file to create
            media_data: Base64 encoded data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_bytes = base64.b64decode(media_data)
            with open(file_name, "wb") as f:
                f.write(file_bytes)
            return True
        except Exception as e:
            print(f"Failed to save media file: {e}")
            return False

    def _register_story_in_database(self, file_name, media_type):
        """
        Register story metadata in database.

        Args:
            file_name: Name of story file
            media_type: 'video' or 'photo'

        Returns:
            bool: True if successful, False otherwise
        """
        db_content_type = "image" if media_type == "photo" else "video"

        payload = {
            "username": self.username,
            "filename": file_name,
            "content_type": db_content_type
        }

        response = self._send_request("ADD_STORY", payload)
        return response.get('status') == 'success'

    def _upload_and_verify_story(self, file_name):
        """
        Upload story to server and verify.

        Args:
            file_name: Name of file to upload
        """
        time.sleep(TWO_SECOND_PAUSE)

        try:
            import transfer_story_to_server
            transfer_story_to_server.run(file_name, self.username)

            time.sleep(TWO_SECOND_PAUSE)
            self.verify_story_uploaded(file_name)

        except Exception as e:
            print(f"Failed to upload media: {e}")

    def _cleanup_file(self, file_name):
        """
        Remove file from filesystem.

        Args:
            file_name: Name of file to remove
        """
        try:
            if os.path.exists(file_name):
                os.remove(file_name)
        except:
            pass

    def verify_story_uploaded(self, filename):
        """
        Periodically checks if the newly uploaded story
         is available on the server.

        Args:
            filename: Name of the uploaded file

        Returns:
            bool: True if story found, False otherwise
        """
        for i in range(ATTEMPTS_LIMIT):
            response = self._send_request('GET_STORIES', {})

            if response.get('status') == 'success':
                stories = response.get('stories', [])
                for story in stories:
                    if story['username'] == self.username:
                        return True

            time.sleep(HALF_SECOND_DELAY)

        return False

    def run(self):
        """
        Main entry point for the application - REFACTORED.
        Launches the GUI interface.
        """
        # Create the wx app
        app = wx.App()

        # Show login screen
        if not self._show_login_screen(app):
            return  # User cancelled

        # Show main menu
        self._show_main_menu(app)

        # Exit cleanly
        sys.exit(EXIT_CODE_SUCCESS)

    def _show_login_screen(self, app):
        """
        Display login/signup screen.

        Args:
            app: wx.App instance

        Returns:
            bool: True if login successful, False if cancelled
        """
        login_frame = LoginSignupFrame(self)
        login_frame.Show()
        app.MainLoop()

        # Check if login was successful
        return getattr(login_frame, "login_successful", False)

    def _show_main_menu(self, app):
        """
        Display main menu after successful login.

        Args:
            app: wx.App instance
        """
        from MainMenuFrame import MainMenuFrame

        main_menu = MainMenuFrame(username=self.username, client_ref=self)
        main_menu.Show()

        # Run GUI main loop
        app.MainLoop()


if __name__ == '__main__':
    import sys
    import os

    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(PATH_LIST_HEAD, current_dir)

    try:
        from Video_Player_Client import run_video_player_client

        client_app = Client()
        client_app.run()
    except ImportError as e:
        print(f"✗ CRITICAL ERROR: Required video player modules missing: {e}")
        print(f"Current directory: {current_dir}")
        print(f"Files in directory: {os.listdir(current_dir)}")
        sys.exit(EXIT_CODE_ERROR)
