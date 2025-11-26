import socket
import base64
import os
import json
import struct
from pathlib import Path


class MediaServer:
    def __init__(self, host='127.0.0.1', port=3333):
        self.host = host
        self.port = port
        self.server_socket = None

    def start(self):
        """Start the server and listen for ONE connection only"""

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)

        print(f"Server listening on {self.host}:{self.port}")

        try:
            # Accept only ONE connection
            client_socket, address = self.server_socket.accept()
            print(f"\nNew connection from {address}")
            self.handle_client(client_socket)

        except KeyboardInterrupt:
            print("\nShutting down server...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Close server socket after handling one client
            print("Closing server socket...")
            self.server_socket.close()
            print("Server closed. Returning to run()")

    def handle_client(self, client_socket):
        """Handle incoming client connection"""

        try:
            # First receive the size of the payload (4 bytes)
            size_data = client_socket.recv(4)
            if not size_data:
                return

            payload_length = struct.unpack('!I', size_data)[0]
            print(f"Expecting payload of {payload_length:,} bytes")

            # Receive the actual payload
            received_data = b''
            while len(received_data) < payload_length:
                chunk = client_socket.recv(min(4096, payload_length - len(received_data)))
                if not chunk:
                    break
                received_data += chunk

            # Parse the JSON payload
            payload = json.loads(received_data.decode('utf-8'))

            print(f"Received {payload['media_type']} - Size: {payload['size']:,} characters")

            # Decode and save the received media
            media_type = payload['media_type']
            base64_data = payload['data']

            # Decode base64 to bytes
            file_bytes = base64.b64decode(base64_data)

            # Determine file extension
            extension = '.mp4' if media_type == 'video' else '.jpg'
            output_filename = f"received_{media_type}_{len(file_bytes)}{extension}"

            # Save to file
            with open(output_filename, 'wb') as f:
                f.write(file_bytes)

            print(f"Saved to {output_filename} ({len(file_bytes):,} bytes)")

            # Send confirmation
            response = "OK: Media received successfully"
            client_socket.send(response.encode('utf-8'))

        except Exception as e:
            print(f"Error handling client: {e}")
            try:
                client_socket.send(f"ERROR: {e}".encode('utf-8'))
            except:
                pass

        finally:
            # Close the client socket after handling
            print("Closing client connection...")
            client_socket.close()


def run():
    print("Starting media server...")
    server = MediaServer(host='127.0.0.1', port=3333)
    server.start()
    print("Returned to run() - Server cycle completed")

    # פה אני רוצה שנוסיף קריאה להעלאה של הסטורי בשרת (פונקציה מתוך server)


if __name__ == '__main__':
    run()
