import socket
import json
import os
import sys
from Video_player import play_video_with_system_audio

# --- Configuration ---
HOST = '127.0.0.1'  # Localhost IP
PORT = 5000
VIDEO_FOLDER = "videos"  # Folder where video files are expected to be saved locally


class Client:
    """
    Client class for the Tennis Social application.
    Handles connection, user interface, and sending requests to the server.
    """

    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.username = None
        self.is_admin = 0  # 0 for regular user, 1 for admin

        # Ensure the video folder exists
        if not os.path.exists(VIDEO_FOLDER):
            os.makedirs(VIDEO_FOLDER)

    def _send_request(self, request_type, payload):
        """
        Sends a JSON request to the server and returns the server's JSON response.
        """
        try:
            # Create a socket connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))

            # Prepare request data as JSON
            request_data = json.dumps({
                "type": request_type,
                "payload": payload
            }).encode('utf-8')

            # Send data to the server
            client_socket.sendall(request_data)

            # Receive the response
            response_data = client_socket.recv(4096).decode('utf-8')
            response = json.loads(response_data)

            client_socket.close()
            return response

        except ConnectionRefusedError:
            print(f"❌ Error: Could not connect to the server at {self.host}:{self.port}. Is the server running?")
            # We don't exit here, just return an error state
            return {"status": "error", "message": "Connection Refused."}
        except json.JSONDecodeError:
            print("❌ Error: Received non-JSON or corrupted data from the server.")
            return {"status": "error", "message": "Invalid server response format."}
        except Exception as e:
            print(f"❌ An unexpected error occurred during request: {e}")
            return {"status": "error", "message": f"Network Error: {e}"}

    # --- Authentication Methods ---

    def signup(self):
        """Handles user registration."""
        print("\n--- Signup ---")
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()

        # Optional: Ask if the user should be an admin (only for initial testing/setup)
        is_admin_input = input("Register as admin? (y/N): ").strip().lower()
        is_admin = 1 if is_admin_input == 'y' else 0

        response = self._send_request('SIGNUP', {'username': username, 'password': password, 'is_admin': is_admin})

        if response.get('status') == 'success':
            print(f"✅ {response['message']}")
        else:
            print(f"❌ Signup failed: {response.get('message', 'Unknown error')}")

    def login(self):
        """Handles user login."""
        print("\n--- Login ---")
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()

        response = self._send_request('LOGIN', {'username': username, 'password': password})

        if response.get('status') == 'success':
            self.username = username
            return True
        else:
            print(f"❌ Login failed: {response.get('message', 'Unknown error')}")
            return False

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
            print(f"❌ Could not retrieve videos: {response.get('message', 'No videos found or server error.')}")
            return

        videos = response['videos']
        print("\n--- Available Videos ---")

        if not videos:
            print("No videos have been uploaded yet.")
            return

        for i, video in enumerate(videos):
            # Display title, uploader, category, level, and fetch likes count
            likes_res = self._send_request('GET_LIKES_COUNT', {'video_title': video['title']})
            likes_count = likes_res.get('count', 0)

            print(
                f"[{i + 1}] Title: {video['title']} | Category: {video['category']} | Level: {video['level']} | Uploader: {video['uploader']} | Likes: {likes_count}")

        # Allow user to select a video to play
        while True:
            selection = input("Enter video number to select, or (B)ack: ").strip().upper()
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
        category = input("Enter category (forehand/backhand/serve/slice/volley/smash): ").strip().lower()
        level = input("Enter difficulty (easy/medium/hard): ").strip().lower()

        # The uploader is the currently logged-in user
        payload = {
            'title': title,
            'category': category,
            'level': level,
            'uploader': self.username  # Must send the uploader's username
        }

        response = self._send_request('ADD_VIDEO', payload)

        if response.get('status') == 'success':
            print(f"✅ {response['message']}")
        else:
            print(f"❌ Upload failed: {response.get('message', 'Unknown error')}")

    # --- Interaction and Playback ---

    def handle_video_interaction(self, video_data):
        """Handles actions (Play, Like, Comment) after a video is selected."""
        video_title = video_data['title']

        print(f"\n--- Interacting with: {video_title} ---")
        print("1. Play Video (Simulated)")
        print("2. Toggle Like/Unlike")
        print("3. View/Add Comments")
        print("4. Back to Video List")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            # Simulate playing the video file (requires the file to exist locally)
            print(f"▶️ Playing video: {video_title}...")
            # We assume the file is available locally for the player simulation
            # The client only manages metadata, not file transfer, in this simple model.
            video_path = os.path.join(VIDEO_FOLDER, video_title)

            # Simple simulation: just call the player with a placeholder path
            play_video_with_system_audio(video_path)
            print(f"⏹️ Finished playing: {video_title}")

        elif choice == '2':
            self.toggle_like(video_title)

        elif choice == '3':
            self.view_and_add_comments(video_title)

        elif choice == '4':
            return

        else:
            print("Invalid choice.")

        # Loop back to interaction menu to allow chaining actions
        self.handle_video_interaction(video_data)

    def toggle_like(self, video_title):
        """Toggles the like status for the video."""
        payload = {
            'username': self.username,
            'title': video_title
        }
        response = self._send_request('LIKE_VIDEO', payload)

        if response.get('status') == 'success':
            print(f"👍 {response['message']}")
        else:
            print(f"❌ Action failed: {response.get('message', 'Unknown error')}")

    def view_and_add_comments(self, video_title):
        """Retrieves and allows adding comments."""
        # 1. Get and display comments
        response = self._send_request('GET_COMMENTS', {'video_title': video_title})

        print(f"\n--- Comments for {video_title} ---")
        if response.get('status') == 'success' and response.get('comments'):
            for comment in response['comments']:
                print(f"[{comment['timestamp']}] {comment['username']}: {comment['content']}")
        else:
            print("No comments yet.")

        # 2. Allow user to add a new comment
        comment_content = input("\nAdd a new comment (or press Enter to skip): ").strip()

        if comment_content:
            payload = {
                'username': self.username,
                'video_title': video_title,
                'content': comment_content
            }
            add_res = self._send_request('ADD_COMMENT', payload)

            if add_res.get('status') == 'success':
                print("✅ Comment added.")
            else:
                print(f"❌ Failed to add comment: {add_res.get('message', 'Error.')}")

    # --- Stories Management ---

    def display_stories(self):
        """Retrieves and displays all active stories (last 24 hours)."""
        response = self._send_request('GET_STORIES', {})

        print("\n--- Live Stories (Last 24h) ---")

        if response.get('status') != 'success' or not response.get('stories'):
            print(f"❌ Could not retrieve stories: {response.get('message', 'No active stories found.')}")
            return

        stories = response['stories']
        for i, story in enumerate(stories):
            print(f"[{i + 1}] {story['username']} posted a story at {story['timestamp']}")

        # Allow user to view content (simple print simulation)
        while True:
            selection = input("Enter story number to view content, or (B)ack: ").strip().upper()
            if selection == 'B':
                return

            try:
                index = int(selection) - 1
                if 0 <= index < len(stories):
                    print(f"\n--- Story Content from {stories[index]['username']} ---")
                    print(f"💬 {stories[index]['content']}")
                    print("---------------------------------")
                    break
                else:
                    print("Invalid number.")
            except ValueError:
                print("Invalid input.")

    def add_story(self):
        """Sends an ADD_STORY request to the server."""
        print("\n--- Post a New Story ---")
        content = input("Enter story text (e.g., 'Great practice today!'): ").strip()

        if not content:
            print("Story content cannot be empty.")
            return

        payload = {
            'username': self.username,
            'content': content
        }

        response = self._send_request('ADD_STORY', payload)

        if response.get('status') == 'success':
            print(f"✅ {response['message']}")
        else:
            print(f"❌ Failed to post story: {response.get('message', 'Unknown error')}")

    # --- Manager Commands ---

    def view_all_users(self):
        """Retrieves and displays all users (Manager only)."""
        if not self.is_admin:
            print("🛑 Access denied. Only managers can view all users.")
            return

        response = self._send_request('GET_ALL_USERS', {})

        if response.get('status') != 'success' or not response.get('users'):
            print(f"❌ Could not retrieve users: {response.get('message', 'Server error.')}")
            return

        print("\n--- All Registered Users (MANAGER VIEW) ---")
        for user in response['users']:
            admin_status = "MANAGER" if user['is_admin'] else "Regular User"
            print(f"Username: {user['username']} | Status: {admin_status}")
        print("------------------------------------------")

    # --- Main Loop ---

    def run(self):
        """Main client application loop."""

        # Initial authentication
        while self.username is None:
            # שינוי ההנחיה: שימוש במילים מלאות
            print("\nWelcome! Choose: (Signup) / (Login)")

            # Ensure choice is properly stripped and uppercase for robust input
            choice = input("Your choice: ").strip().upper()

            # Filter out empty or non-SIGNUP/LOGIN choices immediately
            if not choice:
                print("Invalid choice. Try again.")
                continue

            # בדיקה מול מילים מלאות
            if choice == "SIGNUP":
                self.signup()
            elif choice == "LOGIN":
                if self.login():
                    # After successful login, attempt to get admin status
                    users_res = self._send_request('GET_ALL_USERS', {})
                    if users_res.get('users'):
                        # Find the current user's admin status
                        for user in users_res['users']:
                            if user['username'] == self.username:
                                self.is_admin = user['is_admin']
                                break
                    print(
                        f"\nWelcome {self.username}! You are logged in as a {'regular user' if not self.is_admin else 'manager'}.")
            else:
                print("Invalid choice. Try again.")

        # Main menu loop
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

    # --- Helper Method for Stories Menu ---
    def display_stories_menu(self):
        """Menu for stories functionality."""
        print("\n--- Stories Menu ---")
        print("1. View live stories")
        print("2. Post a new story")
        print("3. Back to Main Menu")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            self.display_stories()
        elif choice == '2':
            self.add_story()
        elif choice == '3':
            return
        else:
            print("Invalid choice.")


if __name__ == '__main__':
    # play_video_with_system_audio() # Removed initial unnecessary call

    # Check if the Video_player module is ready
    if 'Video_player' in sys.modules:
        # If the video player system is imported, proceed with the client app
        client_app = Client()
        client_app.run()
    else:
        # This occurs if the necessary video player component is missing or failed to import
        print("❌ CRITICAL ERROR: The Video_player module is required but could not be loaded.")
        sys.exit(1)
