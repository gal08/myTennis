import requests
import os
from Video_player import play_video_with_system_audio

# Base URL of the Flask server
BASE_URL = "http://127.0.0.1:5000/"


def signup():
    """
    Register a new user (regular or admin).
    If user chooses admin, they must enter the correct admin password.
    """
    role = input("Choose user type (regular / admin): ").strip().lower()
    is_admin = 0
    if role == "admin":
        admin_pass = input("Enter admin signup password: ").strip()
        if admin_pass == "secret123":
            is_admin = 1
        else:
            print("Incorrect admin password. You will be logged in as regular user.")

    username = input("Username: ").strip()
    password = input("Password: ").strip()
    valid_password = input("Enter your password again: ").strip()
    if password == valid_password:
        return username, password, is_admin
    return None, None, None


def upload_video(username, password):
    """
    Allow an admin to upload a new video by providing title, category and level.
    """
    print("\nEnter video details to upload:")
    title = input("Title: ").strip()
    category = input("Category: ").strip()
    level = input("Level: ").strip()

    video_data = {
        "username": username,
        "password": password,
        "title": title,
        "category": category,
        "level": level
    }

    res = requests.post(BASE_URL + "/api/videos", json=video_data)
    print("Upload response:", res.json())


def check_admin(username_to_check, users):
    """
    Checks if a given username is an admin based on the list of users from the server.
    """
    for user in users:
        if user["username"] == username_to_check:
            return user["is_admin"]
    return False


def main():
    print("Welcome! Choose: signup / login")
    choice = input("Your choice: ").strip().upper()

    if choice not in ["SIGNUP", "LOGIN"]:
        print("Invalid choice")
        return

    # Test connection to server
    res = requests.get(BASE_URL + "/")
    print("Server says:", res.text)

    username = None
    password = None

    # Signup process
    if choice == "SIGNUP":
        username, password, is_admin = signup()
        if not username:
            print("Signup failed – passwords didn't match")
            return

        new_user = {
            "username": username,
            "password": password,
            "is_admin": is_admin
        }
        res = requests.post(BASE_URL + "/api/register", json=new_user)
        print("Register:", res.json())

    # Login process
    elif choice == "LOGIN":
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        login_data = {"username": username, "password": password}
        res = requests.post(BASE_URL + "/api/login", json=login_data)
        print("Login:", res.json())

    # Check if user is admin
    users_res = requests.get(BASE_URL + "/api/users")
    users_data = users_res.json()

    if username and password:
        login_successful = "error" not in res.json()

        # Admin menu
        if login_successful and check_admin(username, users_data):
            print(f"\nWelcome admin {username}! You can upload videos.")
            upload_video(username, password)

        # Regular user menu
        elif login_successful:
            print(f"\nWelcome {username}! You are logged in as a regular user.")

            # Get available videos
            videos_res = requests.get(BASE_URL + "/api/videos")
            videos = videos_res.json()

            if not videos:
                print("No videos available.")
                return

            print("\nAvailable Videos:")
            for i, video in enumerate(videos):
                print(f"{i+1}. {video['title']} ({video['category']} - {video['level']})")

            try:
                # User chooses video to watch
                choice = int(input("Select a video to play (number): ")) - 1
                selected_video = videos[choice]['title']
                video_path = os.path.join("videos", selected_video + ".mp4")

                if os.path.exists(video_path):
                    play_video_with_system_audio(video_path)

                    # Ask if user wants to like the video
                    like = input("Would you like to like this video? (yes/no): ").strip().lower()
                    if like == "yes":
                        like_res = requests.post(BASE_URL + "/api/like", json={
                            "username": username,
                            "title": selected_video
                        })
                        print("Like:", like_res.json().get("message", "Something went wrong."))
                else:
                    print("Video file not found locally.")
            except (IndexError, ValueError):
                print("Invalid selection.")

        else:
            print("Login/signup failed.")


if __name__ == "__main__":
    main()
