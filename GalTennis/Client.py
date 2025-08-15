import socket  # For TCP communication with the server
import requests
# Server connection details
BASE_URL = "http://127.0.0.1:5000/"


"""def send_request(command, username, password, is_admin=0):
    Connects to the server and sends a command with username, password, and admin flag.
    Prints the response received from the server.
    # Create a TCP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to the server
        sock.connect((IP, PORT))

        # Build the message to send (e.g. "SIGNUP alice Pass123 0")
        message = f"{command} {username} {password} {is_admin}"

        # Send the message as bytes
        sock.send(message.encode())

        # Receive the server's response
        response = sock.recv(1024).decode()

        # Display the server's reply
        print("Server response:", response)
"""


def signup():
    role = input("Choose user type (regular / admin): ").strip().lower()
    if role == "admin":
        admin_pass = input("Enter admin signup password: ").strip()
        if admin_pass == "secret123":  # Admin signup password
            is_admin = 1
        else:
            print("Incorrect admin password. You will be login as regular user.")

    username = input("Username: ").strip()
    password = input("Password: ").strip()
    vaild_password = input("enter your password again: ").strip()
    if(password == vaild_password):
        list = [username, password]
        return list
    return []

def main():
    """
    Main function that asks the user to choose between SIGNUP and LOGIN,
    collects credentials, and sends the request.
    If SIGNUP is chosen, user is also asked to choose between regular and admin user.
    """
    print("Welcome! Choose: signup / login")
    choice = input("Your choice: ").strip().upper()

    # Validate user choice
    if choice not in ["SIGNUP", "LOGIN"]:
        print("Invalid choice")
        return

    is_admin = 0  # Default: regular user
    res = requests.get(BASE_URL + "/")
    print("Server says:", res.text)

    # If the user chooses to sign up, ask for user type
    if choice == "SIGNUP":
        details = signup()
        new_user = {
            "username": details[0],
            "password": details[1]
        }
        res = requests.post(BASE_URL + "/register", json=new_user)
        print("Register:", res.json())

        res = requests.get(BASE_URL + "/users")
        print("Users:", res.json())
    else:
        # Ask for username and password
        username = input("Username: ").strip()
        password = input("Password: ").strip()

    # Send the request to the server
    """send_request(choice, username, password, is_admin)"""

# Start the client program
if __name__ == "__main__":
    main()
