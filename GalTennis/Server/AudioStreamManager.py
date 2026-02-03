"""
Gal Haham
Audio Stream Manager
Handles audio extraction and streaming using FFmpeg
"""
import subprocess
import numpy as np

AUDIO_DEFAULT_SAMPLE_RATE = 44100
AUDIO_DEFAULT_CHANNELS = 2
BYTES_PER_SAMPLE_16BIT = 2
FFMPEG_STDOUT_BUFFER_BYTES = 100000000
MAX_SPLITS_FOR_KEY_VALUE = 1


class AudioStreamManager:

    def __init__(self, video_path):
        self.video_path = video_path
        self.audio_process = None
        self.audio_info = None
        self.audio_chunk_size = None
        self.samples_per_frame = None

    def extract_audio_info(self):
        try:
            result = self._run_ffprobe()
            info = self._parse_ffprobe_output(result)

            sample_rate = self._safe_get_int(
                info, 'sample_rate', AUDIO_DEFAULT_SAMPLE_RATE
            )
            channels = self._safe_get_int(
                info, 'channels', AUDIO_DEFAULT_CHANNELS
            )

            self.audio_info = {
                'sample_rate': sample_rate,
                'channels': channels,
                'codec': info.get('codec_name', 'unknown'),
            }

            return self.audio_info

        except FileNotFoundError:
            return self._get_default_audio_info()

        except:
            return self._get_default_audio_info()

    def setup_audio_extraction(self, fps):
        try:
            if not self.audio_info:
                self.extract_audio_info()

            self.samples_per_frame = int(self.audio_info['sample_rate'] / fps)
            self.audio_chunk_size = (
                    self.samples_per_frame *
                    self.audio_info['channels'] *
                    BYTES_PER_SAMPLE_16BIT
            )

            ffmpeg_cmd = [
                'ffmpeg',
                '-i', self.video_path,
                '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', str(self.audio_info['sample_rate']),
                '-ac', str(self.audio_info['channels']),
                '-f', 's16le',
                'pipe:1'
            ]

            try:
                self.audio_process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    bufsize=FFMPEG_STDOUT_BUFFER_BYTES
                )
                return True
            except FileNotFoundError:
                return False
            except:
                return False
        except:
            return False

    def read_audio_chunk(self):
        try:
            if not self.audio_process or not self.audio_process.stdout:
                return None

            audio_data = self.audio_process.stdout.read(self.audio_chunk_size)
            if audio_data and len(audio_data) == self.audio_chunk_size:
                return np.frombuffer(audio_data, dtype=np.int16)
            else:
                return None
        except:
            return None

    def close(self):
        try:
            if self.audio_process:
                try:
                    self.audio_process.terminate()
                    self.audio_process.wait()
                except:
                    pass
                self.audio_process = None
        except:
            pass

    def has_audio(self):
        try:
            return self.audio_process is not None
        except:
            return False

    def get_audio_info(self):
        try:
            return {
                'audio_sample_rate': self.audio_info['sample_rate'],
                'audio_channels': self.audio_info['channels'],
                'samples_per_frame': self.samples_per_frame,
                'has_audio': self.has_audio()
            }
        except:
            return {
                'audio_sample_rate': AUDIO_DEFAULT_SAMPLE_RATE,
                'audio_channels': AUDIO_DEFAULT_CHANNELS,
                'samples_per_frame': 0,
                'has_audio': False
            }

    def _run_ffprobe(self):
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=sample_rate,channels,codec_name',
                '-of', 'default=noprint_wrappers=1',
                self.video_path
            ]
            return subprocess.run(cmd, capture_output=True, text=True, check=True)
        except:
            raise

    @staticmethod
    def _parse_ffprobe_output(result):
        try:
            info = {}
            for line in result.stdout.splitlines():
                if '=' in line:
                    k, v = line.strip().split('=', MAX_SPLITS_FOR_KEY_VALUE)
                    info[k] = v
            return info
        except:
            return {}

    @staticmethod
    def _safe_get_int(info_dict, key, default_value):
        try:
            return int(info_dict.get(key, default_value))
        except:
            return default_value

    @staticmethod
    def _get_default_audio_info():
        return {
            'sample_rate': AUDIO_DEFAULT_SAMPLE_RATE,
            'channels': AUDIO_DEFAULT_CHANNELS,
            'codec': 'unknown',
        }