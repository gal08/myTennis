"""
Gal Haham
Real-time audio recording manager using PyAudio.
Supports simultaneous recording with video,
WAV file saving, and resource cleanup.
"""
import pyaudio
import wave
AUDIO_CHANNELS = 2
STANDARD_SAMPLE_RATE = 44100
CHUNK_SIZE = 1024


class AudioRecorder:
    """ A class that handles real-time audio recording using PyAudio.

    This class is designed to be used while recording video at the same time.
    It allows starting and stopping an audio stream, saving the audio as a WAV
    file, and cleaning up resources safely after recording is finished.
    """

    def __init__(self):
        """Initialize the audio recorder and all required settings."""
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False

        self.format = pyaudio.paInt16
        self.channels = AUDIO_CHANNELS
        self.rate = STANDARD_SAMPLE_RATE
        self.chunk = CHUNK_SIZE

    def start_recording(self):
        """Start the audio recording process."""
        self.frames = []
        self.is_recording = True

        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
                stream_callback=self._audio_callback
            )
            self.stream.start_stream()
            print("Audio recording started")
        except Exception as e:
            print(f"Failed to start audio recording: {e}")
            self.is_recording = False

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Internal callback function that receives audio frames"""
        if self.is_recording:
            self.frames.append(in_data)
        return in_data, pyaudio.paContinue

    def stop_recording(self):
        """Stop the current recording session."""
        self.is_recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        print("Audio recording stopped")

    def save_audio(self, filename):
        """Save the recorded audio data to a WAV file."""
        if not self.frames:
            print("No audio data to save")
            return False

        try:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            print(f"Audio saved to {filename}")
            return True
        except Exception as e:
            print(f"Failed to save audio: {e}")
            return False

    def cleanup(self):
        """Release all audio resources.

        This method:
        - Closes the stream if needed.
        - Terminates the PyAudio instance.

        Must be called when recording is fully done."""
        if self.stream:
            self.stream.close()
        self.audio.terminate()