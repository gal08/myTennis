"""
Gal Haham
Video Player Client - Main Entry Point
FIXED: Prevents multiple players running simultaneously.
FIXED: Uses updated receive-only VideoAudioClient.
"""
import threading
from Video_Audio_Client import VideoAudioClient

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9999

_current_player_thread = None
_player_lock = threading.Lock()


def run_video_player_client(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """
    Launch video player in a background thread.
    Only one player runs at a time - call again after closing the current one.
    """
    global _current_player_thread

    with _player_lock:
        if _current_player_thread and _current_player_thread.is_alive():
            print("[PlayerClient] Video already playing - close current window first")
            return

        def _play():
            try:
                client = VideoAudioClient(host, port)
                if client.connect():
                    print("[PlayerClient] Connected, starting playback...")
                    client.play_stream()
                else:
                    print("[PlayerClient] Failed to connect to video server")
            except ConnectionError as e:
                print(f"[PlayerClient] Connection error: {e}")
            except Exception as e:
                print(f"[PlayerClient] Unexpected error: {e}")

        _current_player_thread = threading.Thread(
            target=_play,
            daemon=False,           # Keep process alive while video is playing
            name="VideoPlayerThread"
        )
        _current_player_thread.start()
        print("[PlayerClient] Video player started")


if __name__ == '__main__':
    import time
    run_video_player_client()
    try:
        print("Press Ctrl+C to exit...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")