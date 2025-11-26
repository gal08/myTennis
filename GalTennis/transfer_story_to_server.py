import socket
import base64
import os
import json
import struct
from pathlib import Path


class MediaClient:
    def __init__(self, host='127.0.0.1', port=3333):
        self.host = host
        self.port = port

    def send_media(self, file_path):
        """Send media file to server"""

        # Create a new socket for this connection
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            print(f"Connecting to {self.host}:{self.port}...")
            client_socket.connect((self.host, self.port))
            print("Connected!")

            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File {file_path} not found")

            print(f"Preparing {file_path}...")

            # Read file and convert to base64
            with open(file_path, 'rb') as file:
                file_bytes = file.read()
                file_base64 = base64.b64encode(file_bytes).decode('utf-8')

            # Calculate payload size
            payload_size = len(file_base64)

            # Identify file type
            file_extension = Path(file_path).suffix.lower()
            media_type = 'video' if file_extension in ['.mp4', '.avi', '.mov', '.mkv'] else 'image'

            # Create payload
            payload = {
                'size': payload_size,
                'media_type': media_type,
                'data': file_base64
            }

            print(f"Payload ready: {payload_size:,} characters")

            # Convert payload to JSON bytes
            payload_json = json.dumps(payload).encode('utf-8')
            payload_length = len(payload_json)

            # Send the size first (4 bytes, network byte order)
            client_socket.send(struct.pack('!I', payload_length))

            # Send the actual payload
            print(f"Sending {payload_length:,} bytes...")
            client_socket.sendall(payload_json)
            print("Sent!")

            # Wait for server response
            response = client_socket.recv(1024).decode('utf-8')
            print(f"Server response: {response}")

        except Exception as e:
            print(f"Error: {e}")

        finally:
            client_socket.close()
            print("Connection closed\n")


def run(file_path):
    client = MediaClient()
    client.send_media(file_path)


if __name__ == '__main__':
    run("C:\CyberProject\GIT\myTennis\GalTennis\serve_hard_6.mp4")

