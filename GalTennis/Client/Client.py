"""
Gal Haham
Main client for Tennis Social application.
Handles server connection, menus, video upload/viewing,
stories, and user authentication.
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
from Show_all_stories_in_wx import run
# --- Import the Story camera module we integrated ---
from Story_camera import StoryCameraFrame

# --- Configuration ---
HOST = readServerIp()
PORT = 5000
VIDEO_FOLDER = "videos"
DISPLAY_INDEX_OFFSET = 1
ADMIN = 1
REGULAR = 0
ZERO_COUNT = 0
ZERO_INDEX = 0
ONE_BASED_OFFSET = 1
TWO_SECOND_PAUSE = 2
ATTEMPTS_LIMIT = 5
HALF_SECOND_DELAY = 0.5
PATH_LIST_HEAD = 0
EXIT_CODE_ERROR = 1
GET_VIDEOS_PHOTOS = 5


class Client:
    """
    Client class for the Tennis Social application.
    Handles connection, user interface, and sending requests to the server.
    """

    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.username = None
        self.is_admin = REGULAR
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
            error_msg = (
                f"Error: Could not connect to the server at "
                f"{self.host}:{self.port}. Is the server running?"
            )

            print(error_msg)

            return {"status": "error", "message": "Connection Refused."}
        except json.JSONDecodeError:
            error_msg = (
                f"Error: Could not connect to the server at "
                f"{self.host}:{self.port}. Is the server running?"
            )

            print(error_msg)

            return {
                "status": "error",
                "message": (
                    "Invalid server response format."
                )
            }

        except Exception as e:
            print(f"An unexpected error occurred during request: {e}")
            return {"status": "error", "message": f"Network Error: {e}"}

    # --- Video Management Methods ---

    def display_video_menu(self):
        """Displays the video browsing menu."""
        print("\n--- Video Menu ---")
        print("1. View all videos")
        print("2. Upload a new video")
        print("3. Back to Main Menu")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            self.view_videos()
        elif choice == '2':
            self.upload_video_metadata()
        elif choice == '3':
            return
        else:
            print("Invalid choice.")

    def view_videos(self):
        """Retrieves and displays the list of videos from the server."""
        response = self._send_request('GET_VIDEOS', {})

        if response.get('status') != 'success' or not response.get('videos'):
            error_message = response.get(
                "message",
                "No videos found or server error."
            )

            print(
                f"✗ Could not retrieve videos: {error_message}"
            )

            return

        videos = response['videos']
        print("\n--- Available Videos ---")

        if not videos:
            print("No videos have been uploaded yet.")
            return

        for i, video in enumerate(videos):
            request_payload = {
                "video_title": video["title"]
            }

            likes_res = self._send_request(
                "GET_LIKES_COUNT",
                request_payload
            )

            likes_count = likes_res.get('count', ZERO_COUNT)

            video_index_to_display = i + DISPLAY_INDEX_OFFSET

            video_title = video["title"]
            video_category = video["category"]
            video_level = video["level"]
            video_uploader = video["uploader"]

            message = (
                f"[{video_index_to_display}] "
                f"Title: {video_title} | "
                f"Category: {video_category} | "
                f"Level: {video_level} | "
                f"Uploader: {video_uploader} | "
                f"Likes: {likes_count}"
            )

            print(message)

        while True:
            user_input = input(
                "Enter video number to select, or (B)ack: "
            )

            selection = user_input.strip().upper()

            if selection == 'B':
                return

            try:
                index = int(selection) - ONE_BASED_OFFSET
                if ZERO_INDEX <= index < len(videos):
                    self.handle_video_interaction(videos[index])
                    break
                else:
                    print("Invalid number.")
            except ValueError:
                print("Invalid input.")

    def upload_video_metadata(self):
        """Collects metadata and sends the ADD_VIDEO request to the server."""
        print("\n--- Upload Video Metadata ---")
        title = input("Enter video filename (e.g., my_serve_1.mp4): ").strip()
        category_prompt = (
            "Enter category "
            "(forehand/backhand/serve/slice/volley/smash): "
        )

        category_input = input(category_prompt)

        category = category_input.strip().lower()

        level = input("Enter difficulty (easy/medium/hard): ").strip().lower()

        payload = {
            'title': title,
            'category': category,
            'level': level,
            'uploader': self.username
        }

        response = self._send_request('ADD_VIDEO', payload)

        if response.get('status') == 'success':
            print(f"✓ {response['message']}")
        else:
            error_message = response.get('message', 'Unknown error')

            print(
                f"✗ Upload failed: {error_message}"
            )

    # --- Interaction and Playback ---

    def handle_video_interaction(self, video_data):
        """Handles actions (Play, Like, Comment) after a video is selected."""
        video_title = video_data['title']

        print(f"\n--- Interacting with: {video_title} ---")
        print("1. Play Video")
        print("2. Toggle Like/Unlike")
        print("3. View/Add Comments")
        print("4. Back to Video List")

        choice = int(input("Enter choice: "))

        if choice == 1:
            print(f"▶ Playing video: {video_title}...")

            # Request server to start streaming this video
            response = self._send_request(
                'PLAY_VIDEO',
                {
                    'video_title': video_title
                }
            )

            if response.get('status') == 'success':
                # Wait for server to initialize
                time.sleep(TWO_SECOND_PAUSE)

                # Start client player (blocking until video ends)
                run_video_player_client()

                print(f"ℹ Finished playing: {video_title}")
            else:
                print(
                    f"✗ Failed to play video: "
                    f"{response.get('message', 'Unknown error')}"
                )

        elif choice == 2:
            self.toggle_like(video_title)

        elif choice == 3:
            self.view_and_add_comments(video_title)

        elif choice == 4:
            return

        else:
            print("Invalid choice.")

        self.handle_video_interaction(video_data)

    def toggle_like(self, video_title):
        """Toggles the like status for the video."""
        payload = {
            'username': self.username,
            'title': video_title
        }
        response = self._send_request('LIKE_VIDEO', payload)

        if response.get('status') == 'success':
            print(f"❤ {response['message']}")
        else:
            print(
                f"✗ Action failed: "
                f"{response.get('message', 'Unknown error')}"
            )

    def view_and_add_comments(self, video_title):
        """Retrieves and allows adding comments."""
        response = self._send_request(
            'GET_COMMENTS',
            {'video_title': video_title}
        )

        print(f"\n--- Comments for {video_title} ---")
        if response.get('status') == 'success' and response.get('comments'):
            for comment in response['comments']:
                print(
                    f"[{comment['timestamp']}] "
                    f"{comment['username']}: "
                    f"{comment['content']}"
                )

        else:
            print("No comments yet.")

        comment_content = input(
            "\nAdd a new comment (or press Enter to skip): "
        ).strip()

        if comment_content:
            payload = {
                'username': self.username,
                'video_title': video_title,
                'content': comment_content
            }
            add_res = self._send_request('ADD_COMMENT', payload)

            if add_res.get('status') == 'success':
                print("✓ Comment added.")
            else:
                print(
                    f"✗ Failed to add comment: "
                    f"{add_res.get('message', 'Error.')}"
                )

    # --- Stories Management ---

    def display_all_stories(self):
        response = self._send_request('GET_IMAGES_OF_ALL_VIDEOS', {})

        if response.get('status') != 'success':
            print(
                f"✗ Could not retrieve stories: "
                f"{response.get('message', 'Server error.')}"
            )

            return
        Show_all_stories_in_wx.run()


    def display_stories(self):
        """Retrieves and displays all available
        stories from the stories folder."""
        response = self._send_request('GET_STORIES', {})

        print("\n--- Available Stories ---")

        if response.get('status') != 'success':
            print(
                f"✗ Could not retrieve stories: "
                f"{response.get('message', 'Server error.')}"
            )

            return

        stories = response.get('stories', [])

        if not stories:
            print("No stories found in the stories folder.")
            print(
                "Tip: Add images (.jpg, .png) or videos (.mp4) "
                "to the 'stories' folder"
            )

            return

        # Display all available stories
        for i, story in enumerate(stories):
            # Determine file type
            ext = os.path.splitext(story['filename'])[1].lower()
            file_type = (
                "📷 Image"
                if ext in ['.jpg', '.jpeg', '.png', '.bmp']
                else "🎥 Video"
            )

            print(
                f"[{i + 1}] "
                f"{file_type} | "
                f"{story['filename']} | "
                f"From: {story['username']} | "
                f"{story['timestamp']}"
            )

        while True:
            selection = input(
                "\nEnter story number to view, or (B)ack: "
            ).strip().upper()

            if selection == 'B':
                return

            try:
                index = int(selection) - ONE_BASED_OFFSET
                if ZERO_INDEX <= index < len(stories):
                    selected_story = stories[index]
                    print(
                        f"\n▶ Playing story: {selected_story['filename']}..."
                    )

                    self.play_story(selected_story['filename'])

                    print("\n--- Available Stories ---")
                    for i, story in enumerate(stories):
                        ext = os.path.splitext(story['filename'])[1].lower()
                        is_image = ext in ['.jpg', '.jpeg', '.png', '.bmp']

                        file_type = (
                            "Image"
                            if is_image
                            else "Video"
                        )

                        story_index = i + ONE_BASED_OFFSET
                        story_file = story['filename']
                        story_user = story['username']
                        story_time = story['timestamp']

                        print(
                            f"[{story_index}] {file_type} | {story_file} | "
                            f"From: {story_user} | {story_time}"
                        )

                else:
                    print("Invalid number.")
            except ValueError:
                print("Invalid input.")

    def play_story(self, story_filename):
        """Plays a story (image or video)"""
        print(f"▶ Loading story: {story_filename}...")

        story_request_type = 'PLAY_STORY'
        story_payload = {'filename': story_filename}

        response = self._send_request(story_request_type, story_payload)

        if response.get('status') == 'success':
            time.sleep(TWO_SECOND_PAUSE)

            run_story_player_client()

            print(f"ℹ Finished playing story: {story_filename}")
        else:
            error_prefix = "✗ Failed to play story: "
            error_message = response.get('message', 'Unknown error')

            print(f"{error_prefix}{error_message}")

    def on_story_post_callback(self, caption, media_type, media_data):
        print("Posting story...")

        if media_type == "video":
            file_name = "story.mp4"
        else:
            file_name = "story.jpg"

        try:
            file_bytes = base64.b64decode(media_data)
            with open(file_name, "wb") as f:
                f.write(file_bytes)
            print(f"✓ Saved temp file: {file_name}")
        except Exception as e:
            print(f"✗ Failed to save media file: {e}")
            return

        db_content_type = "image" if media_type == "photo" else "video"

        payload = {
            "username": self.username,
            "filename": file_name,
            "content_type": db_content_type
        }
        res = self._send_request("ADD_STORY", payload)

        if res.get('status') != 'success':
            print(f"✗ Failed to register story: {res.get('message')}")
            try:
                os.remove(file_name)
            except:
                pass
            return

        print("✓ Story registered in database")

        print("Waiting for media server to start...")
        time.sleep(TWO_SECOND_PAUSE)

        try:
            import transfer_story_to_server
            transfer_story_to_server.run(file_name, self.username)
            print("✓ Story uploaded to media server!")

            print("Finalizing...")
            time.sleep(TWO_SECOND_PAUSE)

            self.verify_story_uploaded(file_name)

        except Exception as e:
            print(f"✗ Failed to upload media: {e}")
            print("Story metadata saved but media upload failed.")

        finally:
            try:
                if os.path.exists(file_name):
                    os.remove(file_name)
                    print(f"Cleaned up temp file: {file_name}")
            except Exception as e:
                print(f"⚠ Could not delete temp file: {e}")

    def verify_story_uploaded(self, filename):
        """
            Periodically checks if the newly uploaded
            story is already available
            on the server."""
        print("Verifying story availability...", end="", flush=True)

        for i in range(ATTEMPTS_LIMIT):
            response = self._send_request('GET_STORIES', {})

            if response.get('status') == 'success':
                stories = response.get('stories', [])

                for story in stories:
                    if story['username'] == self.username:
                        print(" ✓ Story ready!")
                        return True

            print(".", end="", flush=True)
            time.sleep(HALF_SECOND_DELAY)

        print(" ⚠ Story uploaded but may take a moment to appear")
        return False

    def open_story_camera(self):
        """Opens story camera as separate process"""
        print("Opening camera...")

        story_posted = False

        import tempfile
        import pickle

        # Create temp file for callback data
        callback_file = os.path.join(
            tempfile.gettempdir(),
            f'story_callback_{self.username}_{time.time()}.pkl'
        )

        try:
            # Get path to Story_camera.py
            camera_script = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'Story_camera.py'
            )

            print(f"[DEBUG] Running camera: {camera_script}")
            print("[DEBUG] Close the camera window when done.")

            # Run as subprocess with its own wx.App
            import subprocess
            result = subprocess.run(
                [sys.executable, camera_script, self.username, callback_file],
                cwd=os.path.dirname(camera_script)
            )

            print(f"[DEBUG] Camera closed (exit code: {result.returncode})")

            # Check if story was posted
            if os.path.exists(callback_file):
                try:
                    with open(callback_file, 'rb') as f:
                        callback_data = pickle.load(f)

                    if callback_data.get('posted'):
                        story_posted = True
                        caption = callback_data.get('caption', '')
                        media_type = callback_data.get('media_type')
                        media_data = callback_data.get('media_data')

                        print("[DEBUG] Story data received from subprocess")
                        self.on_story_post_callback(
                            caption,
                            media_type,
                            media_data
                        )

                    # Clean up temp file
                    os.remove(callback_file)
                    print("[DEBUG] Cleaned up callback file")

                except Exception as e:
                    print(f"[DEBUG] Error reading callback: {e}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            print(f"✗ Camera error: {e}")
            import traceback
            traceback.print_exc()

        if story_posted:
            print("\n✓ Story posted! Returning to menu...")
        else:
            print("\n✗ Camera closed without posting")

    def view_all_users(self):
        """Retrieves and displays all users (Manager only)."""
        if not self.is_admin:
            print("Access denied. Only managers can view all users.")
            return

        response = self._send_request('GET_ALL_USERS', {})

        if response.get('status') != 'success' or not response.get('users'):
            error_prefix = "✗ Could not retrieve users: "
            error_message = response.get('message', 'Server error.')
            print(f"{error_prefix}{error_message}")

            return

        print("\n--- All Registered Users (MANAGER VIEW) ---")
        for user in response['users']:
            admin_status = "MANAGER" if user['is_admin'] else "Regular User"
            print(f"Username: {user['username']} | Status: {admin_status}")
        print("------------------------------------------")

    # --- Main Loop ---

    def run(self):
        """Main client application loop."""

        # Show GUI login/signup
        app = wx.App()
        login_frame = LoginSignupFrame(self)
        app.MainLoop()

        # Check if login was successful
        if not login_frame.login_successful or not self.username:
            print("Login cancelled or failed. Exiting...")
            return

        role_name = "regular user" if not self.is_admin else "manager"

        welcome_prefix = "\n✓ Welcome "
        welcome_suffix = f"! You are logged in as a {role_name}."

        print(f"{welcome_prefix}{self.username}{welcome_suffix}")

        # Continue with console menu
        while True:
            try:
                print("\n--- Main Menu ---")
                print("1. Videos (View/Upload)")
                print("2. Stories (View/Post)")
                if self.is_admin:
                    print("M. Manager Commands (View All Users)")
                print("Q. Quit")

                choice = input("Enter choice: ").strip().upper()

                if choice == '1':
                    self.display_video_menu()
                elif choice == '2':
                    self.display_stories_menu()
                elif choice == 'M' and self.is_admin:
                    self.view_all_users()
                elif choice == 'Q':
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice.")
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"✗ Error in main menu: {e}")
                import traceback
                traceback.print_exc()
                print("Returning to menu...")

    def display_stories_menu(self):
        """Menu for stories functionality."""
        print("\n--- Stories Menu ---")
        print("1. choose one story to show")
        print("2. Post a new story (open camera)")
        print("3. open all stories wx")
        print("4. Back to Main Menu")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            self.display_stories()
        elif choice == '2':
            # Open the camera UI (integrated)
            self.open_story_camera()
        elif choice == '3':
            self.display_all_stories()
        elif choice == '4':
            return
        else:
            print("Invalid choice.")


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
