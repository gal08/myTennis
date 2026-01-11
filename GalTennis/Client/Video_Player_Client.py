"""
Gal Haham
Video & audio streaming client - Main Entry Point
FIXED: Prevents multiple video players from running simultaneously
"""
import threading
from Video_Audio_Client import VideoAudioClient

# Server configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9999

# Global variable to track if a video is already playing
_current_player_thread = None
_player_lock = threading.Lock()


def run_video_player_client(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """
    Run the video player client - connects directly to stream without GUI.
    Ensures only ONE video plays at a time.
    """
    global _current_player_thread

    with _player_lock:
        # Check if a video is already playing
        if _current_player_thread and _current_player_thread.is_alive():
            print("Video already playing! Close current video first.")
            return

        def play_in_background():
            client = VideoAudioClient(host, port)
            if client.connect():
                print("Connected to video stream")
                client.play_stream()
            else:
                print("Failed to connect to video stream")

        # Start playback in a new thread
        _current_player_thread = threading.Thread(
            target=play_in_background,
            daemon=False,
            name="VideoPlayerThread"
        )
        _current_player_thread.start()
        print("Video player started")


if __name__ == '__main__':
    run_video_player_client()

    # Keep main thread alive
    import time
    try:
        print("Press Ctrl+C to exit...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")