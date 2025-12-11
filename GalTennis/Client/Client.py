"""
Gal Haham
Main client for Tennis Social application.
Handles server connection and provides backend services for GUI.
Primary entry point for the application.
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


class Client:
    """
    Client class for the Tennis Social application.
    Provides backend services for the GUI interface.
    """

    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.username = None
        self.is_admin = 0
        if not os.path.exists(VIDEO_FOLDER):
            os.makedirs(VIDEO_FOLDER)

    def _send_request(self, request_type, payload):
        """
        Sends a JSON request to the server using Protocol
        and returns the server's JSON response.
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
            return {"status": "error", "message": "Connection Refused. Is server running?"}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid server response format."}
        except Exception as e:
            return {"status": "error", "message": f"Network Error: {e}"}

    # --- Story Post Callback (used by Story_camera.py) ---

    def on_story_post_callback(self, caption, media_type, media_data):
        """
        Callback for posting a story from the camera.
        Called by Story_camera.py after capturing media.
        """
        if media_type == "video":
            file_name = "story.mp4"
        else:
            file_name = "story.jpg"

        try:
            file_bytes = base64.b64decode(media_data)
            with open(file_name, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            print(f"Failed to save media file: {e}")
            return

        db_content_type = "image" if media_type == "photo" else "video"

        payload = {
            "username": self.username,
            "filename": file_name,
            "content_type": db_content_type
        }
        res = self._send_request("ADD_STORY", payload)

        if res.get('status') != 'success':
            try:
                os.remove(file_name)
            except:
                pass
            return

        time.sleep(TWO_SECOND_PAUSE)

        try:
            import transfer_story_to_server
            transfer_story_to_server.run(file_name, self.username)

            time.sleep(TWO_SECOND_PAUSE)
            self.verify_story_uploaded(file_name)

        except Exception as e:
            print(f"Failed to upload media: {e}")

        finally:
            try:
                if os.path.exists(file_name):
                    os.remove(file_name)
            except:
                pass

    def verify_story_uploaded(self, filename):
        """
        Periodically checks if the newly uploaded story is available on the server.
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

    # --- Main Entry Point ---

    def run(self):
        """
        Main entry point for the application.
        Launches the GUI interface.
        """
        import wx

        # Create the wx app once
        app = wx.App()

        # ---------------------
        # LOGIN SCREEN
        # ---------------------
        login_frame = LoginSignupFrame(self)
        login_frame.Show()
        app.MainLoop()

        # After login window closes:
        if not getattr(login_frame, "login_successful", False):
            # User cancelled login - just exit quietly
            return

        # ---------------------
        # MAIN MENU GUI
        # ---------------------
        from MainMenuFrame import MainMenuFrame

        main_menu = MainMenuFrame(username=self.username, client_ref=self)
        main_menu.Show()

        # Run GUI main loop
        app.MainLoop()

        # After main menu closes - exit quietly
        # (goodbye message shown in GUI dialog)

        # Force exit to close all background threads
        import sys
        sys.exit(0)


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