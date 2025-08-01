import socket  # For TCP communication with the server

# Server connection details
IP = "127.0.0.1"  # Server IP address
PORT = 1730  # Server port


def send_request(command, username, password, is_admin=0):
    """
    Connects to the server and sends a command with username, password, and admin flag.
    Prints the response received from the server.
    """
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

    # If the user chooses to sign up, ask for user type
    if choice == "SIGNUP":
        role = input("Choose user type (regular / admin): ").strip().lower()
        if role == "admin":
            admin_pass = input("Enter admin signup password: ").strip()
            if admin_pass == "secret123":  # Admin signup password
                is_admin = 1
            else:
                print("Incorrect admin password. You will be signed up as regular user.")

    # Ask for username and password
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    # Send the request to the server
    send_request(choice, username, password, is_admin)


# Start the client program
if __name__ == "__main__":
    main()
