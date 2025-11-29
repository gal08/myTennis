import socket
import json
import os
import sys
import threading
import time
import wx
import base64

import transfer_story_to_server
from Protocol import Protocol
from Video_Player_Client import run_video_player_client
from story_player_client import run_story_player_client

# --- Import the Story camera module we integrated ---
import Story_camera

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 5000
VIDEO_FOLDER = "videos"
DISPLAY_INDEX_OFFSET = 1


class LoginSignupFrame(wx.Frame):
    """GUI for Login and Signup"""

    def __init__(self, client_instance):
        super().__init__(
            None,
            title="Tennis Social - Login",
            size=wx.Size(450, 400)
        )
        self.client = client_instance
        self.login_successful = False

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(245, 245, 245))

        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        title_font = wx.Font(
            18,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD
        )

        title = wx.StaticText(panel, label="🎾 Tennis Social")
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(40, 120, 80))
        main_sizer.Add(title, 0, wx.ALL | wx.CENTER, 20)

        # Notebook for tabs
        notebook = wx.Notebook(panel)

        # --- Login Tab ---
        login_panel = wx.Panel(notebook)
        login_sizer = wx.BoxSizer(wx.VERTICAL)

        # Username
        login_sizer.Add(
            wx.StaticText(login_panel, label="Username:"),
            0,
            wx.LEFT | wx.TOP,
            10
        )

        self.login_username = wx.TextCtrl(login_panel, size=wx.Size(300, 30))
        login_sizer.Add(self.login_username, 0, wx.ALL | wx.EXPAND, 10)

        # Password
        login_sizer.Add(
            wx.StaticText(login_panel, label="Password:"),
            0,
            wx.LEFT,
            10
        )

        self.login_password = wx.TextCtrl(
            login_panel,
            size=wx.Size(300, 30),
            style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER
        )

        login_sizer.Add(self.login_password, 0, wx.ALL | wx.EXPAND, 10)

        # Login button
        login_btn = wx.Button(
            login_panel,
            label="Login",
            size=wx.Size(300, 40)
        )

        login_btn.SetBackgroundColour(wx.Colour(76, 175, 80))
        login_btn.SetForegroundColour(wx.WHITE)
        login_btn.Bind(wx.EVT_BUTTON, self.on_login)
        login_sizer.Add(login_btn, 0, wx.ALL | wx.EXPAND, 10)

        # Status label for login
        self.login_status = wx.StaticText(login_panel, label="")
        self.login_status.SetForegroundColour(wx.Colour(200, 0, 0))
        login_sizer.Add(self.login_status, 0, wx.ALL | wx.CENTER, 10)

        login_panel.SetSizer(login_sizer)
        notebook.AddPage(login_panel, "Login")

        # --- Signup Tab ---
        signup_panel = wx.Panel(notebook)
        signup_sizer = wx.BoxSizer(wx.VERTICAL)

        # Username
        signup_sizer.Add(
            wx.StaticText(signup_panel, label="Username:"),
            0,
            wx.LEFT | wx.TOP,
            10
        )

        self.signup_username = wx.TextCtrl(signup_panel, size=wx.Size(300, 30))
        signup_sizer.Add(self.signup_username, 0, wx.ALL | wx.EXPAND, 10)

        # Password
        signup_sizer.Add(
            wx.StaticText(signup_panel, label="Password:"),
            0,
            wx.LEFT,
            10
        )

        self.signup_password = wx.TextCtrl(
            signup_panel,
            size=wx.Size(300, 30),
            style=wx.TE_PASSWORD
        )

        signup_sizer.Add(self.signup_password, 0, wx.ALL | wx.EXPAND, 10)

        # Admin checkbox
        self.admin_checkbox = wx.CheckBox(
            signup_panel,
            label="Register as Manager/Admin"
        )

        signup_sizer.Add(self.admin_checkbox, 0, wx.ALL, 10)

        # Admin secret (initially hidden)
        signup_sizer.Add(
            wx.StaticText(
                signup_panel,
                label="Admin Secret Key:"
            ),
            0,
            wx.LEFT,
            10
        )

        self.admin_secret = wx.TextCtrl(
            signup_panel,
            size=wx.Size(300, 30),
            style=wx.TE_PASSWORD
        )

        self.admin_secret.Enable(False)
        signup_sizer.Add(self.admin_secret, 0, wx.ALL | wx.EXPAND, 10)

        # Bind checkbox event
        self.admin_checkbox.Bind(wx.EVT_CHECKBOX, self.on_admin_checkbox)

        # Signup button
        signup_btn = wx.Button(
            signup_panel,
            label="Sign Up",
            size=wx.Size(300, 40)
        )

        signup_btn.SetBackgroundColour(wx.Colour(33, 150, 243))
        signup_btn.SetForegroundColour(wx.WHITE)
        signup_btn.Bind(wx.EVT_BUTTON, self.on_signup)
        signup_sizer.Add(signup_btn, 0, wx.ALL | wx.EXPAND, 10)

        # Status label for signup
        self.signup_status = wx.StaticText(signup_panel, label="")
        self.signup_status.SetForegroundColour(wx.Colour(200, 0, 0))
        signup_sizer.Add(self.signup_status, 0, wx.ALL | wx.CENTER, 10)

        signup_panel.SetSizer(signup_sizer)
        notebook.AddPage(signup_panel, "Sign Up")

        main_sizer.Add(notebook, 1, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(main_sizer)

        self.Centre()
        self.Show()

        # Bind Enter key for login
        self.login_password.Bind(wx.EVT_TEXT_ENTER, self.on_login)

    def on_admin_checkbox(self, event):
        """Enable/disable admin secret field based on checkbox"""
        self.admin_secret.Enable(self.admin_checkbox.GetValue())

    def on_login(self, event):
        """Handle login button click"""
        username = self.login_username.GetValue().strip()
        password = self.login_password.GetValue().strip()

        if not username or not password:
            self.login_status.SetLabel("⚠ Please enter username and password")
            return

        self.login_status.SetLabel("Logging in...")
        self.login_status.SetForegroundColour(wx.Colour(100, 100, 100))
        wx.SafeYield()

        response = self.client._send_request('LOGIN', {
            'username': username,
            'password': password
        })

        if response.get('status') == 'success':
            self.client.username = username

            # Get user admin status
            users_res = self.client._send_request('GET_ALL_USERS', {})
            if users_res.get('users'):
                for user in users_res['users']:
                    if user['username'] == username:
                        self.client.is_admin = user['is_admin']
                        break

            self.login_status.SetLabel("✓ Login successful!")
            self.login_status.SetForegroundColour(wx.Colour(0, 150, 0))
            self.login_successful = True

            wx.CallLater(500, self.Close)
        else:
            error_message = response.get('message', 'Login failed')

            self.login_status.SetLabel(
                f"✗ {error_message}"
            )

            self.login_status.SetForegroundColour(wx.Colour(200, 0, 0))

    def on_signup(self, event):
        """Handle signup button click"""
        username = self.signup_username.GetValue().strip()
        password = self.signup_password.GetValue().strip()
        is_admin = 1 if self.admin_checkbox.GetValue() else 0

        if not username or not password:
            self.signup_status.SetLabel("⚠ Please enter username and password")
            return

        if is_admin and not self.admin_secret.GetValue().strip():
            self.signup_status.SetLabel("⚠ Admin secret key required")
            return

        self.signup_status.SetLabel("Creating account...")
        self.signup_status.SetForegroundColour(wx.Colour(100, 100, 100))
        wx.SafeYield()

        payload = {
            'username': username,
            'password': password,
            'is_admin': is_admin
        }

        if is_admin:
            payload['admin_secret'] = self.admin_secret.GetValue().strip()

        response = self.client._send_request('SIGNUP', payload)

        if response.get('status') == 'success':
            self.signup_status.SetLabel("✓ Account created! Please login.")
            self.signup_status.SetForegroundColour(wx.Colour(0, 150, 0))

            # Clear fields
            self.signup_username.SetValue("")
            self.signup_password.SetValue("")
            self.admin_secret.SetValue("")
            self.admin_checkbox.SetValue(False)
            self.admin_secret.Enable(False)
        else:
            signup_error_message = response.get('message', 'Signup failed')

            self.signup_status.SetLabel(
                f"✗ {signup_error_message}"
            )

            self.signup_status.SetForegroundColour(wx.Colour(200, 0, 0))


class Client:
    """
    Client class for the Tennis Social application.
    Handles connection, user interface, and sending requests to the server.
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

            likes_count = likes_res.get('count', 0)

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
                index = int(selection) - 1
                if 0 <= index < len(videos):
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

        choice = input("Enter choice: ").strip()

        if choice == '1':
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
                time.sleep(2)

                # Start client player (blocking until video ends)
                run_video_player_client()

                print(f"ℹ Finished playing: {video_title}")
            else:
                print(
                    f"✗ Failed to play video: "
                    f"{response.get('message', 'Unknown error')}"
                )

        elif choice == '2':
            self.toggle_like(video_title)

        elif choice == '3':
            self.view_and_add_comments(video_title)

        elif choice == '4':
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
            print(f" {response['message']}")
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
                "Image"
                if ext in ['.jpg', '.jpeg', '.png', '.bmp']
                else "Video"
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
                index = int(selection) - 1
                if 0 <= index < len(stories):
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
                            " Image"
                            if is_image
                            else "🎥 Video"
                        )

                        story_index = i + 1
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
            time.sleep(2)

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
        time.sleep(2)

        try:
            import transfer_story_to_server
            transfer_story_to_server.run(file_name, self.username)
            print("✓ Story uploaded to media server!")

            print("Finalizing...")
            time.sleep(2)

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
        print("Verifying story availability...", end="", flush=True)

        for i in range(5):
            response = self._send_request('GET_STORIES', {})

            if response.get('status') == 'success':
                stories = response.get('stories', [])

                for story in stories:
                    if story['username'] == self.username:
                        print(" ✓ Story ready!")
                        return True

            print(".", end="", flush=True)
            time.sleep(0.5)

        print(" ⚠ Story uploaded but may take a moment to appear")
        return False

    def open_story_camera(self):
        """Opens story camera - creates new wx.App instance"""
        print("Opening camera...")

        story_posted = {'posted': False}
        camera_closed = {'closed': False}

        def on_post(caption, media_type, media_data):
            story_posted['posted'] = True
            self.on_story_post_callback(caption, media_type, media_data)

        def on_camera_closed():
            camera_closed['closed'] = True

        app = wx.App()

        frame = Story_camera.StoryCameraFrame(
            None,
            self.username,
            on_post,
            on_camera_closed
        )

        frame.Show()

        app.MainLoop()

        app.Destroy()

        if story_posted['posted']:
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

    def display_stories_menu(self):
        """Menu for stories functionality."""
        print("\n--- Stories Menu ---")
        print("1. View live stories")
        print("2. Post a new story (open camera)")
        print("3. Back to Main Menu")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            self.display_stories()
        elif choice == '2':
            # Open the camera UI (integrated)
            self.open_story_camera()
        elif choice == '3':
            return
        else:
            print("Invalid choice.")


if __name__ == '__main__':
    try:
        from Video_Player_Client import run_video_player_client

        client_app = Client()
        client_app.run()
    except ImportError as e:
        print(f"✗ CRITICAL ERROR: Required video player modules missing: {e}")
        sys.exit(1)
