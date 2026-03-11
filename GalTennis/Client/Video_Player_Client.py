"""
Gal Haham
Video Player Client - Main Entry Point
REFACTORED: Single-port design. Requires a ticket from the server so
            VideoAudioClient knows which video to request.
"""
import threading
from Video_Audio_Client import VideoAudioClient

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9999

_current_player_thread = None
_player_lock = threading.Lock()


def run_video_player_client(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    ticket: str = "",
):
    """
    Launch video player in a background thread.
    Only one player runs at a time - call again after closing the current one.

    Args:
        host:   Server IP address
        port:   Server port (always 9999 now)
        ticket: One-time ticket string returned by PLAY_VIDEO response
    """
    global _current_player_thread

    with _player_lock:
        if _current_player_thread and _current_player_thread.is_alive():
            print("[PlayerClient] Video already playing - close current window first")
            return

        def _play():
            try:
                client = VideoAudioClient(host, port, ticket=ticket)
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
            daemon=False,
            name="VideoPlayerThread"
        )
        _current_player_thread.start()
        print("[PlayerClient] Video player started")


if __name__ == '__main__':
    import time
    # For standalone testing, provide a ticket manually
    run_video_player_client(ticket="testticket"[:8])
    try:
        print("Press Ctrl+C to exit...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")