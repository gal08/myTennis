import cv2
import os
import time
import numpy as np
import subprocess
import sys
import platform


# --- Helper Functions for CV2 Overlay ---

def create_loading_screen():
    """Create loading screen using NumPy and OpenCV."""
    # Screen is 400x600, 3 color channels (RGB)
    screen = np.zeros((400, 600, 3), dtype=np.uint8)

    # Gradient background (Dark blue/gray)
    for i in range(400):
        color_value = int(50 + (i / 400) * 50)
        screen[i, :] = [color_value // 3, color_value // 2, color_value]  # Blueish gradient

    # Text for the main title
    cv2.putText(screen, "TENNIS VIDEO PLAYER", (120, 180),
                cv2.FONT_HERSHEY_COMPLEX, 1.0, (255, 255, 255), 2)
    # Text for loading status
    cv2.putText(screen, "Loading...", (240, 220),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 200, 255), 2)

    return screen


def create_video_overlay(frame, paused, current_time, total_time, audio_status):
    """Create video control overlay with time, progress bar, and status."""
    height, width = frame.shape[:2]

    # Bottom control area (semi-transparent black)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, height - 60), (width, height), (0, 0, 0), -1)
    frame = cv2.addWeighted(frame, 0.8, overlay, 0.2, 0)  # Blend frames

    # Time display (Current / Total)
    time_text = f"{int(current_time // 60):02d}:{int(current_time % 60):02d} / {int(total_time // 60):02d}:{int(total_time % 60):02d}"
    cv2.putText(frame, time_text, (20, height - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Progress bar calculation
    progress = current_time / total_time if total_time > 0 else 0
    bar_width = width - 300
    bar_start = 200
    # Draw background bar (gray)
    cv2.rectangle(frame, (bar_start, height - 30), (bar_start + bar_width, height - 20), (50, 50, 50), -1)
    # Draw progress bar (blue)
    cv2.rectangle(frame, (bar_start, height - 30), (bar_start + int(bar_width * progress), height - 20), (0, 150, 255),
                  -1)

    # Playback status (PAUSED/PLAYING)
    status = "PAUSED" if paused else "PLAYING"
    color = (100, 100, 255) if paused else (100, 255, 100)  # Reddish if paused, Greenish if playing
    cv2.putText(frame, status, (width - 120, height - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Audio status indicator
    cv2.putText(frame, f"AUDIO: {audio_status}", (width - 150, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                (100, 200, 255), 1)

    # Controls help text
    cv2.putText(frame, "SPACE: Pause | Q: Quit | F: Fullscreen", (20, height - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

    return frame


# --- Audio Player Class ---

class AudioPlayerThread:
    """
    Manages background audio playback using system utilities (VBScript/PowerShell on Windows,
    or a simple 'start' command on other systems) to prevent blocking the main video loop.
    """

    def __init__(self, video_path):
        self.video_path = video_path
        self.process = None
        self.started = False

    def start_audio(self):
        """Starts audio playback in a separate, non-blocking process."""
        system = platform.system()

        if system == "Windows":
            # Use PowerShell to run media player hidden
            try:
                # Command to start media player invisibly and keep it playing for a long duration (999s)
                powershell_cmd = (
                    f'powershell -WindowStyle Hidden -Command '
                    f'"Add-Type -AssemblyName presentationCore; '
                    f'$mediaPlayer = New-Object system.windows.media.mediaplayer; '
                    f'$mediaPlayer.open([uri]\'{os.path.abspath(self.video_path)}\'); '
                    f'$mediaPlayer.Play(); Start-Sleep -Seconds 999"'
                )
                self.process = subprocess.Popen(powershell_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.started = True
                return True
            except Exception as e:
                print(f"Windows Audio start (PowerShell) failed: {e}")
                return False

        elif system in ("Linux", "Darwin"):  # Linux or macOS
            print("Note: Advanced background audio control is limited on non-Windows systems.")
            print("Attempting to use system 'xdg-open' or 'open'...")
            try:
                if system == "Linux":
                    cmd = ['xdg-open', self.video_path]  # Use default app (may open GUI)
                else:  # Darwin (macOS)
                    cmd = ['open', self.video_path]  # Use default app (may open GUI)

                # NOTE: This method may open a visible media player application.
                self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.started = True
                return True
            except Exception as e:
                print(f"Non-Windows Audio start failed: {e}")
                return False

        else:
            print(f"Unsupported OS: {system}. Cannot start background audio.")
            return False

    def cleanup(self):
        """Clean up and stop the background audio process."""
        if self.process:
            try:
                # Terminate the background process
                self.process.terminate()
                print("Background audio stopped.")
            except Exception as e:
                print(f"Error terminating audio process: {e}")


# --- Main Playback Function ---

def play_video_with_system_audio(video_path):
    """
    Plays the video file using OpenCV for the visuals and a separate
    background process for system audio.
    """
    print(f"Looking for file at: {video_path}")

    if not os.path.exists(video_path):
        print(f"File {video_path} not found!")
        return False

    # Show loading screen
    loading_screen = create_loading_screen()
    cv2.imshow('Video Player', loading_screen)
    cv2.waitKey(1000)  # Display for 1 second

    # Start audio player in background
    print("Starting audio player...")
    audio_player = AudioPlayerThread(video_path)
    audio_started = audio_player.start_audio()

    if audio_started:
        print("Audio started in background")
        time.sleep(0.05)  # Give audio a moment to initialize

    # Load video for visual playback
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Cannot open video for visual playback!")
        if audio_player.started:
            audio_player.cleanup()
        return False

    # Video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_time = total_frames / fps if fps > 0 else 0
    delay = max(1, int(1000 / fps) - 5) if fps > 0 else 30

    # --- START OF ASPECT RATIO FIX ---
    # Get original dimensions
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define a target width (e.g., 960px is a good default size)
    TARGET_WIDTH = 960

    if original_width > 0:
        # Calculate new height based on the target width, preserving the aspect ratio
        aspect_ratio = original_height / original_width
        display_width = min(original_width, TARGET_WIDTH)  # Use original width if smaller than target
        display_height = int(display_width * aspect_ratio)
    else:
        # Fallback to a safe default size if dimensions cannot be read
        display_width = 640
        display_height = 480

    if display_height == 0:  # Ensure height is not zero
        display_height = 540

    print(f"Original Resolution: {original_width}x{original_height}. Displaying at: {display_width}x{display_height}")
    # --- END OF ASPECT RATIO FIX ---

    print(f"Playing: {video_path}")
    print(f"Duration: {int(total_time // 60):02d}:{int(total_time % 60):02d}")
    print(f"Audio: {'ON' if audio_started else 'OFF'}")
    print("Note: Use SPACE to pause/play visuals, Q/ESC to quit.")

    # Setup window
    WINDOW_NAME = 'Tennis Video Player'
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_TOPMOST, 1)
    # Set the calculated dynamic size
    cv2.resizeWindow(WINDOW_NAME, display_width, display_height)

    paused = False
    frame_count = 0
    audio_status = "ON" if audio_started else "OFF"

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1

            # ** IMPORTANT: Resize the frame to fit the calculated display size **
            if frame is not None and (frame.shape[1] != display_width or frame.shape[0] != display_height):
                frame = cv2.resize(frame, (display_width, display_height), interpolation=cv2.INTER_LINEAR)

        if 'frame' in locals() and frame is not None:
            current_time = frame_count / fps if fps > 0 else 0
            frame_with_overlay = create_video_overlay(frame, paused, current_time, total_time, audio_status)
            cv2.imshow(WINDOW_NAME, frame_with_overlay)

        key = cv2.waitKey(delay if not paused else 30) & 0xFF

        if key == ord('q') or key == 27:  # Q or ESC key to quit
            break
        elif key == ord(' '):  # SPACE key to pause/play
            paused = not paused
            print(f"Video {'PAUSED' if paused else 'PLAYING'}")
        elif key == ord('f'):  # F key for Fullscreen
            # Toggle fullscreen state
            current_prop = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
            new_prop = cv2.WINDOW_NORMAL if current_prop == cv2.WINDOW_FULLSCREEN else cv2.WINDOW_FULLSCREEN
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, new_prop)

    # Final cleanup
    audio_player.cleanup()
    cap.release()
    cv2.destroyAllWindows()
    return True

# NOTE: The '__main__' block from the user's provided code is removed
# as this file is designed to be imported by Client.py.