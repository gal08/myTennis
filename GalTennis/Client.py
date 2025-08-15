import requests

BASE_URL = "http://127.0.0.1:5000/"

def signup():
    role = input("Choose user type (regular / admin): ").strip().lower()
    is_admin = 0
    if role == "admin":
        admin_pass = input("Enter admin signup password: ").strip()
        if admin_pass == "secret123":  # Admin signup password
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
    for user in users:
        if user["username"] == username_to_check:
            return user["is_admin"]
    return None


def main():
    print("Welcome! Choose: signup / login")
    choice = input("Your choice: ").strip().upper()

    if choice not in ["SIGNUP", "LOGIN"]:
        print("Invalid choice")
        return

    res = requests.get(BASE_URL + "/")
    print("Server says:", res.text)

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

        res = requests.get(BASE_URL + "/api/users")
        print("Users:", res.json())

    elif choice == "LOGIN":
        username = input("Username: ").strip()
        password = input("Password: ").strip()

        login_data = {"username": username, "password": password}
        res = requests.post(BASE_URL + "/api/login", json=login_data)
        print("Login:", res.json())
        res = requests.get(BASE_URL + "/api/users")
        print("Users:", res.json())

    data = res.json()
    if "error" not in data & check_admin(username, res):
        upload_video(username, password)


if __name__ == "__main__":
    main()
