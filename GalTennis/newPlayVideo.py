import wx
import cv2
import threading
import time
import os


def get_video_dimensions(video_path):
    """
    בודק את גודל הסרטון (רוחב וגובה) ומחזיר את המידות.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Cannot open video!")
        return None, None, None

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cap.release()

    print(f"Video dimensions: {width}x{height}")
    print(f"FPS: {fps}")
    print(f"Total frames: {frame_count}")
    if fps > 0:
        print(f"Duration: {frame_count / fps:.2f} seconds")

    return width, height, fps


def play_video_wx(video_path):
    """
    wxPython window that plays a video with proper dimensions.
    Uses OpenCV's built-in video backend with audio support.
    """
    # Get video dimensions first
    video_width, video_height, video_fps = get_video_dimensions(video_path)
    if video_width is None:
        return

    # Set default FPS if invalid
    if video_fps <= 0:
        video_fps = 30.0

    # Global flag to stop video playback
    stop_video = threading.Event()

    def play_video():
        """
        Play video using OpenCV with audio backend
        """
        # Open video with OpenCV (with audio support via CAP_FFMPEG)
        cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print("Cannot open video!")
            return

        # Create window with exact video dimensions
        window_name = "Video Player"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        # Set exact window size to match video
        cv2.resizeWindow(window_name, video_width, video_height)

        # Move window to a nice position
        cv2.moveWindow(window_name, 100, 50)

        print(f"Playing at {video_fps} FPS")
        print(f"Window size: {video_width}x{video_height}")

        # Calculate frame delay in milliseconds
        frame_delay_ms = int(1000.0 / video_fps)

        # Playback loop
        start_time = time.time()
        frame_count = 0

        while not stop_video.is_set():
            loop_start = time.time()

            # Read frame
            ret, frame = cap.read()
            if not ret:
                print("End of video")
                break

            # Display frame
            cv2.imshow(window_name, frame)
            frame_count += 1

            # Calculate time to wait
            elapsed = time.time() - loop_start
            wait_ms = max(1, frame_delay_ms - int(elapsed * 1000))

            # Wait and check for key press or window close
            key = cv2.waitKey(wait_ms) & 0xFF
            if key == ord('q') or key == 27:  # q or ESC
                print("Quit by user")
                break
            elif key == ord(' '):  # Space for pause
                print("Paused - press Space to continue")
                while not stop_video.is_set():
                    key2 = cv2.waitKey(100) & 0xFF
                    if key2 == ord(' '):
                        break
                    elif key2 == ord('q') or key2 == 27:
                        cap.release()
                        cv2.destroyAllWindows()
                        return

            # Check if window was closed (X button)
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("Window closed by user")
                break

        # Cleanup
        cap.release()
        cv2.destroyAllWindows()

        # Show statistics
        actual_time = time.time() - start_time
        expected_time = frame_count / video_fps
        print(f"Finished playing {frame_count} frames")
        print(f"Expected duration: {expected_time:.2f}s")
        print(f"Actual duration: {actual_time:.2f}s")

    class VideoFrame(wx.Frame):
        def __init__(self):
            super(VideoFrame, self).__init__(
                None,
                title="Video Player",
                size=(500, 280)
            )

            panel = wx.Panel(self)
            panel.SetBackgroundColour(wx.Colour(240, 240, 240))

            # Title
            title_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            title = wx.StaticText(panel, label="🎬 Video Player", pos=(20, 15))
            title.SetFont(title_font)

            # Video info
            video_label = wx.StaticText(
                panel,
                label=f"File: {os.path.basename(video_path)}",
                pos=(20, 50)
            )

            size_label = wx.StaticText(
                panel,
                label=f"Size: {video_width} x {video_height} pixels",
                pos=(20, 75)
            )

            fps_label = wx.StaticText(
                panel,
                label=f"Frame Rate: {video_fps:.2f} FPS",
                pos=(20, 100)
            )

            # Instructions
            instructions = wx.StaticText(
                panel,
                label="Controls: SPACE = pause/resume  |  Q/ESC = quit  |  X = close window",
                pos=(20, 130)
            )
            instructions.SetForegroundColour(wx.Colour(100, 100, 100))

            # Audio note
            audio_note = wx.StaticText(
                panel,
                label="Note: Audio support depends on OpenCV build with FFmpeg",
                pos=(20, 155)
            )
            audio_note.SetForegroundColour(wx.Colour(150, 100, 50))
            small_font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
            audio_note.SetFont(small_font)

            # Buttons
            play_btn = wx.Button(panel, label="▶ Play Video", pos=(150, 190), size=(200, 40))
            play_btn.SetBackgroundColour(wx.Colour(76, 175, 80))
            play_btn.SetForegroundColour(wx.WHITE)

            # Bind events
            play_btn.Bind(wx.EVT_BUTTON, self.on_play)
            self.Bind(wx.EVT_CLOSE, self.on_close)

            self.Centre()
            self.Show(True)

        def on_play(self, event):
            stop_video.clear()
            t = threading.Thread(target=play_video)
            t.daemon = True
            t.start()

        def on_close(self, event):
            stop_video.set()
            cv2.destroyAllWindows()
            self.Destroy()

    app = wx.App()
    VideoFrame()
    app.MainLoop()