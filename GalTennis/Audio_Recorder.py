import pyaudio
import wave


class AudioRecorder:
    """
    מחלקה להקלטת אודיו בזמן הקלטת וידאו
    """

    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False

        # הגדרות אודיו
        self.format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100
        self.chunk = 1024

    def start_recording(self):
        """התחלת הקלטה"""
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
        """Callback להקלטת אודיו"""
        if self.is_recording:
            self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    def stop_recording(self):
        """עצירת הקלטה"""
        self.is_recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        print("Audio recording stopped")

    def save_audio(self, filename):
        """שמירת האודיו לקובץ WAV"""
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
        """ניקוי משאבים"""
        if self.stream:
            self.stream.close()
        self.audio.terminate()