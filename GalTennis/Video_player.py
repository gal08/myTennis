import cv2
import os
import time
import numpy as np
import subprocess
import threading
import sys


def create_loading_screen():
    """Create loading screen"""
    screen = np.zeros((400, 600, 3), dtype=np.uint8)

    # Gradient background
    for i in range(400):
        color_value = int(50 + (i / 400) * 50)
        screen[i, :] = [color_value, color_value // 2, color_value // 3]

    cv2.putText(screen, "VIDEO PLAYER", (160, 180),
                cv2.FONT_HERSHEY_COMPLEX, 1.2, (255, 255, 255), 2)
    cv2.putText(screen, "Loading...", (240, 220),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 200, 255), 2)

    return screen


def create_video_overlay(frame, paused, current_time, total_time, audio_status):
    """Create video control overlay"""
    height, width = frame.shape[:2]

    # Bottom overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, height - 60), (width, height), (0, 0, 0), -1)
    frame = cv2.addWeighted(frame, 0.8, overlay, 0.2, 0)

    # Time display
    time_text = f"{int(current_time // 60):02d}:{int(current_time % 60):02d} / {int(total_time // 60):02d}:{int(total_time % 60):02d}"
    cv2.putText(frame, time_text, (20, height - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Progress bar
    progress = current_time / total_time if total_time > 0 else 0
    bar_width = width - 300
    bar_start = 200
    cv2.rectangle(frame, (bar_start, height - 30), (bar_start + bar_width, height - 20), (50, 50, 50), -1)
    cv2.rectangle(frame, (bar_start, height - 30), (bar_start + int(bar_width * progress), height - 20), (0, 150, 255),
                  -1)

    # Status
    status = "PAUSED" if paused else "PLAYING"
    color = (255, 100, 100) if paused else (100, 255, 100)
    cv2.putText(frame, status, (width - 120, height - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Audio indicator
    cv2.putText(frame, f"AUDIO: {audio_status}", (width - 150, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                (100, 200, 255), 1)

    # Controls
    cv2.putText(frame, "SPACE: Pause | Q: Quit | F: Fullscreen", (20, height - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

    return frame


class AudioPlayerThread:
    def __init__(self, video_path):
        self.video_path = video_path
        self.process = None
        self.started = False

    def start_audio(self):
        """Start audio in separate hidden window"""
        try:
            # Create a VBS script to play audio silently
            vbs_content = f'''
Set objShell = CreateObject("WScript.Shell")
objShell.Run "cmd /c start /min """" ""{self.video_path}""", 0, False
            '''

            # Write VBS script
            with open("play_audio.vbs", "w") as f:
                f.write(vbs_content)

            # Run VBS script
            subprocess.Popen(["cscript", "//nologo", "play_audio.vbs"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

            self.started = True
            return True

        except Exception as e:
            print(f"Audio start failed: {e}")
            return False

    def cleanup(self):
        """Clean up temporary files"""
        try:
            if os.path.exists("play_audio.vbs"):
                os.remove("play_audio.vbs")
        except:
            pass


def play_video_with_system_audio(video_path):
    print(f"Looking for file at: {video_path}")
    """Play video with system audio player"""

    if not os.path.exists(video_path):
        print(f"File {video_path} not found!")
        return False

    # Show loading
    loading_screen = create_loading_screen()
    cv2.imshow('Video Player', loading_screen)
    cv2.waitKey(1000)

    # Start audio player
    print("Starting audio player...")
    audio_player = AudioPlayerThread(video_path)
    audio_started = audio_player.start_audio()

    if audio_started:
        print("Audio started in background")
        time.sleep(2)  # Give audio time to start

    # Load video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Cannot open video!")
        return False

    # Video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_time = total_frames / fps if fps > 0 else 0
    delay = int(1000 / fps) if fps > 0 else 30

    print(f"Playing: {video_path}")
    print(f"Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print(f"Duration: {int(total_time // 60):02d}:{int(total_time % 60):02d}")
    print(f"Audio: {'ON' if audio_started else 'OFF'}")
    print("Note: Audio plays in system player, video controls here")

    # Setup window
    cv2.namedWindow('Video Player', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Video Player', 800, 600)

    paused = False
    frame_count = 0
    audio_status = "ON" if audio_started else "OFF"

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1

        if 'frame' in locals() and frame is not None:
            current_time = frame_count / fps if fps > 0 else 0
            frame_with_overlay = create_video_overlay(frame, paused, current_time, total_time, audio_status)
            cv2.imshow('Video Player', frame_with_overlay)

        key = cv2.waitKey(delay if not paused else 30) & 0xFF

        if key == ord('q') or key == 27:  # Quit
            break
        elif key == ord(' '):  # Pause/Play
            paused = not paused
            print("PAUSED" if paused else "PLAYING")
        elif key == ord('f'):  # Fullscreen
            cv2.setWindowProperty('Video Player', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Cleanup
    audio_player.cleanup()
    cap.release()
    cv2.destroyAllWindows()
    return True



def simple_dual_window_approach(video_path):
    """Play video with hidden audio"""
    if not os.path.exists(video_path):
        print(f"File {video_path} not found!")
        return False

    print("Starting video with background audio...")

    # Start audio completely hidden using powershell
    try:
        powershell_cmd = f'powershell -WindowStyle Hidden -Command "Add-Type -AssemblyName presentationCore; $mediaPlayer = New-Object system.windows.media.mediaplayer; $mediaPlayer.open([uri]\'{os.path.abspath(video_path)}\'); $mediaPlayer.Play(); Start-Sleep -Seconds 999"'
        subprocess.Popen(powershell_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(2)  # Wait for audio to start
        print("Background audio started")
    except Exception as e:
        print(f"Background audio failed: {e}")

    # Now start video-only display
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Cannot open video!")
        return False

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_time = total_frames / fps if fps > 0 else 0
    delay = int(1000 / fps) if fps > 0 else 30

    print(f"Playing: {video_path}")
    print(f"Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print(f"Duration: {int(total_time // 60):02d}:{int(total_time % 60):02d}")
    print("Controls: SPACE=pause, Q=quit, F=fullscreen")
    print("Audio plays in background")

    cv2.namedWindow('Video Player', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Video Player', 800, 600)

    paused = False
    frame_count = 0

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1

        if 'frame' in locals() and frame is not None:
            current_time = frame_count / fps if fps > 0 else 0
            frame_with_overlay = create_video_overlay(frame, paused, current_time, total_time, "ON")
            cv2.imshow('Video Player', frame_with_overlay)

        key = cv2.waitKey(delay if not paused else 30) & 0xFF

        if key == ord('q') or key == 27:
            break
        elif key == ord(' '):
            paused = not paused
            print("PAUSED" if paused else "PLAYING")
        elif key == ord('f'):
            cv2.setWindowProperty('Video Player', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    cap.release()
    cv2.destroyAllWindows()
    return True


def get_current_path():
    return os.getcwd()


if __name__ == "__main__":
    # Example usage: specify the full path to the video file
    videoName = input("enter video name: ")
    path = get_current_path()
    video_path = os.path.join(path, "videos", videoName)
    success = simple_dual_window_approach(video_path)
    if success:
        print("Playback finished!")
    else:
        print("Playback failed!")

    print("Goodbye!")
