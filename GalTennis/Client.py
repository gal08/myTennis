import requests
import os
from Video_player import play_video_with_system_audio

# --- Configuration ---
VIDEO_FOLDER = "videos"
BASE_URL = "http://127.0.0.1:5000/"


# --- Functions ---
def signup():
    """Register a new user."""
    role = input("Choose user type (regular / admin): ").strip().lower()
    is_admin = 0
    if role == "admin":
        admin_pass = input("Enter admin signup password: ").strip()
        if admin_pass == "secret123":
            is_admin = 1
        else:
            print("Incorrect admin password. You will be logged in as a regular user.")

    username = input("Username: ").strip()
    password = input("Password: ").strip()
    valid_password = input("Enter your password again: ").strip()
    if password == valid_password:
        return username, password, is_admin
    return None, None, None


def upload_video_to_server(username, password):
    """Allows a user to upload a new video to the server."""
    print("\n=== Video Upload ===")
    filename = input("Enter video filename (e.g. forehand_easy_1.mp4): ").strip()
    category = input("Enter category (forehand, backhand, serve, slice, volley, smash): ").strip().lower()
    difficulty = input("Enter difficulty (easy, medium, hard): ").strip().lower()

    video_data = {
        "username": username,
        "password": password,
        "title": filename,
        "category": category,
        "level": difficulty
    }

    try:
        res = requests.post(BASE_URL + "/api/videos", json=video_data)
        print("Server response:", res.json())
    except Exception as e:
        print("Error sending video to server:", e)


def check_admin(username_to_check, users):
    """Checks if a user is an admin."""
    for user in users:
        if user["username"] == username_to_check:
            return user["is_admin"]
    return False


def main():
    print("Welcome! Choose: signup / login")
    choice = input("Your choice: ").strip().upper()

    if choice not in ["SIGNUP", "LOGIN"]:
        print("Invalid choice.")
        return

    res = requests.get(BASE_URL + "/")
    print("Server says:", res.text)

    username = None
    password = None

    if choice == "SIGNUP":
        username, password, is_admin = signup()
        if not username:
            print("Signup failed – passwords didn't match.")
            return
        new_user = {"username": username, "password": password, "is_admin": is_admin}
        res = requests.post(BASE_URL + "/api/register", json=new_user)
        print("Register:", res.json())
    elif choice == "LOGIN":
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        login_data = {"username": username, "password": password}
        res = requests.post(BASE_URL + "/api/login", json=login_data)
        print("Login:", res.json())

    users_res = requests.get(BASE_URL + "/api/users")
    users_data = users_res.json()

    if username and password:
        login_successful = "error" not in res.json()
        if not login_successful:
            print("Login failed.")
            return

        is_admin = check_admin(username, users_data)
        print(f"\nWelcome {username}! You are logged in as a {'regular user' if not is_admin else 'manager'}.")

        while True:
            print("\nChoose an option:")
            print("1. View available videos")
            print("2. Upload a video")
            print("0. Logout")

            option = input("Your choice: ").strip()

            if option == "1":
                videos_res = requests.get(BASE_URL + "/api/videos")
                videos = videos_res.json()

                if not videos:
                    print("No videos available.")
                    continue

                print("\nAvailable Videos:")
                for i, video in enumerate(videos):
                    print(f"{i + 1}. {video['title']} ({video['category']} - {video['level']})")

                try:
                    choice = int(input("Select a video to play (number): ")) - 1
                    selected_video_title = videos[choice]['title']
                    video_path = os.path.join(VIDEO_FOLDER, selected_video_title)

                    if os.path.exists(video_path):
                        play_video_with_system_audio(video_path)
                        like = input("Would you like to like this video? (yes/no): ").strip().lower()
                        if like == "yes":
                            like_res = requests.post(BASE_URL + "/api/like", json={
                                "username": username,
                                "title": selected_video_title
                            })
                            print("Like:", like_res.json().get("message", "Something went wrong."))
                    else:
                        print("Video file not found locally.")
                except (IndexError, ValueError):
                    print("Invalid selection.")

            elif option == "2":
                upload_video_to_server(username, password)

            elif option == "0":
                print("Logging out...")
                break

            else:
                print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()