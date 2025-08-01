import cv2


def play_video(path):
    """
    Plays a video file using OpenCV.

    Args:
        path (str): Full path to the video file.
    """
    # Open the video file
    cap = cv2.VideoCapture(path)

    # Check if the video was opened successfully
    if not cap.isOpened():
        print("Failed to open video.")
        return

    print("▶️ Playing video. Press 'q' to quit.")

    # Read and display each frame until the video ends or 'q' is pressed
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Video", frame)

        # Press 'q' to exit playback
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    # Release resources and close the video window
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Example usage: specify the full path to the video file
    play_video(r"C:\CyberProject\CyberProject\videos\forehand_easy_1.mp4")
