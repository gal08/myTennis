import socket
import os
import cv2
import time
import pickle
import struct
import subprocess
import numpy as np

STORY_SERVER_HOST = '0.0.0.0'
STORY_SERVER_PORT = 6001
STORY_FOLDER = "stories"


def extract_audio_info(video_path):
    """Get audio info using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=sample_rate,channels',
            '-of', 'default=noprint_wrappers=1',
            video_path
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        info = {}
        for line in result.stdout.splitlines():
            if '=' in line:
                k, v = line.strip().split('=', 1)
                info[k] = v

        return {
            'sample_rate': int(info.get('sample_rate', 44100)),
            'channels': int(info.get('channels', 2))
        }
    except:
        return {'sample_rate': 44100, 'channels': 2}


def send_image_story(client_socket, image_path):
    """Send static image as a story"""
    try:
        print(f" Reading image: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            print(f" Error: Could not read image")
            return False

        img = cv2.resize(img, (640, 480))

        # Send story info
        story_info = {
            'type': 'IMAGE',
            'width': 640,
            'height': 480,
            'fps': 30.0,
            'total_frames': 150,  # 5 seconds at 30fps
            'has_audio': False
        }

        info_data = pickle.dumps(story_info)
        client_socket.sendall(struct.pack("!L", len(info_data)))
        client_socket.sendall(info_data)
        print(f"✓ Story info sent: {story_info}")

        # Send frames
        print(f"Sending {story_info['total_frames']} frames...")
        for i in range(story_info['total_frames']):
            _, buffer = cv2.imencode(
                '.jpg',
                img,
                [cv2.IMWRITE_JPEG_QUALITY, 80]
            )

            frame_data = buffer.tobytes()

            packet = {
                'frame': cv2.imdecode(
                    np.frombuffer(frame_data, np.uint8),
                    cv2.IMREAD_COLOR
                ),
                'audio': None,
                'frame_number': i
            }

            packet_data = pickle.dumps(packet)
            client_socket.sendall(struct.pack("!L", len(packet_data)))
            client_socket.sendall(packet_data)

            if i % 30 == 0:
                print(f"Sent frame {i}/{story_info['total_frames']}")

            time.sleep(1 / 30)

        print(f"✓ Image story sent successfully")
        return True

    except Exception as e:
        print(f"Error sending image: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_video_story(client_socket, video_path):
    """Send video with audio using single socket"""
    try:
        print(f"🎬 Opening video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video")
            return False

        # Get video info
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 60:
            fps = 30.0

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_delay = 1.0 / fps

        # Get audio info
        audio_info = extract_audio_info(video_path)
        print(f"Audio info: {audio_info}")

        # Calculate audio chunk size
        samples_per_frame = int(audio_info['sample_rate'] / fps)
        # 2 bytes per sample (16-bit)
        audio_chunk_size = samples_per_frame * audio_info['channels'] * 2

        # Start ffmpeg for audio extraction
        audio_process = None
        try:
            ffmpeg_cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # no video
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', str(audio_info['sample_rate']),
                '-ac', str(audio_info['channels']),
                '-f', 's16le',  # raw audio
                'pipe:1'
            ]
            audio_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=100000000
            )
            print("✓ FFmpeg audio process started")
        except Exception as e:
            print(f" Warning: Could not start audio extraction: {e}")

        # Send story info
        story_info = {
            'type': 'VIDEO',
            'width': width,
            'height': height,
            'fps': fps,
            'total_frames': total_frames,
            'has_audio': audio_process is not None,
            'audio_sample_rate': audio_info['sample_rate'],
            'audio_channels': audio_info['channels'],
            'samples_per_frame': samples_per_frame
        }

        info_data = pickle.dumps(story_info)
        client_socket.sendall(struct.pack("!L", len(info_data)))
        client_socket.sendall(info_data)
        print(f"✓ Story info sent")
        print(f"   Video: {width}x{height} @ {fps:.2f} FPS")
        print(
            f"   Audio: {audio_info['sample_rate']} Hz, "
            f"{audio_info['channels']} ch"
        )

        print(f"   Has Audio: {story_info['has_audio']}")

        # Send frames with audio
        frame_count = 0
        start_time = time.time()

        while True:
            frame_start = time.time()
            ret, frame = cap.read()
            if not ret:
                print(f"End of video at frame {frame_count}")
                break

            # Resize frame
            frame = cv2.resize(frame, (640, 480))

            # Get audio chunk
            audio_chunk = None
            if audio_process and audio_process.stdout:
                try:
                    audio_data = audio_process.stdout.read(audio_chunk_size)
                    if audio_data and len(audio_data) == audio_chunk_size:
                        audio_chunk = np.frombuffer(audio_data, dtype=np.int16)
                except:
                    audio_chunk = None

            # Create and send packet
            packet = {
                'frame': frame,
                'audio': audio_chunk,
                'frame_number': frame_count
            }

            packet_data = pickle.dumps(packet)
            client_socket.sendall(struct.pack("!L", len(packet_data)))
            client_socket.sendall(packet_data)

            frame_count += 1

            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                print(f"Frame {frame_count}/{total_frames} ({elapsed:.1f}s)")

            # Frame rate control
            elapsed = time.time() - frame_start
            sleep_time = max(0, frame_delay - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

        # Cleanup
        cap.release()
        if audio_process:
            audio_process.terminate()
            audio_process.wait()

        print(f"✓ Video story sent successfully ({frame_count} frames)")
        return True

    except Exception as e:
        print(f"Error sending video: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_story_player_server(story_filename):
    """Main server function"""
    story_path = os.path.join(STORY_FOLDER, story_filename)

    print(f"Starting story server")
    print(f"Story: {story_filename}")
    print(f"Path: {story_path}")

    if not os.path.exists(story_path):
        print(f"Error: Story file not found")
        return

    # Check file type
    ext = os.path.splitext(story_filename)[1].lower()
    is_image = ext in ['.jpg', '.jpeg', '.png', '.bmp']
    is_video = ext in ['.mp4', '.avi', '.mov', '.mkv']

    if not is_image and not is_video:
        print(f"Error: Unsupported file format: {ext}")
        return

    print(f"Type: {'IMAGE' if is_image else 'VIDEO'}")

    server_socket = None
    client_socket = None

    try:
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((STORY_SERVER_HOST, STORY_SERVER_PORT))
        server_socket.listen(1)

        print(f"✓ Server listening on {STORY_SERVER_HOST}:{STORY_SERVER_PORT}")
        print(f"Waiting for client...")

        server_socket.settimeout(30)
        client_socket, addr = server_socket.accept()
        print(f"✓ Client connected from {addr}")

        client_socket.settimeout(None)

        # Send story
        if is_image:
            success = send_image_story(client_socket, story_path)
        else:
            success = send_video_story(client_socket, story_path)

        if success:
            print("Story transmission completed successfully")
        else:
            print("Story transmission failed")

    except socket.timeout:
        print("Error: Timeout waiting for client")
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client_socket:
            try:
                client_socket.close()
                print("Client socket closed")
            except:
                pass
        if server_socket:
            try:
                server_socket.close()
                print("Server socket closed")
            except:
                pass
        print("Server shutdown complete")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        run_story_player_server(sys.argv[1])
    else:
        print("Usage: python story_player_server.py <story_filename>")
