import numpy as np
import librosa
import pyaudio
import wave
import sys

def interleave_arrays(a, b):
    c = np.empty((a.size + b.size,), dtype=a.dtype)
    c[0::2] = a
    c[1::2] = b
    return c

def pcm_to_float(sig, dtype='float64'):
    sig = np.asarray(sig)
    if sig.dtype.kind not in 'iu':
        raise TypeError("'sig' must be an array of integers")
    dtype = np.dtype(dtype)
    if dtype.kind != 'f':
        raise TypeError("'dtype' must be a floating point type")

    i = np.iinfo(sig.dtype)
    abs_max = 2 ** (i.bits - 1)
    offset = i.min + abs_max
    return (sig.astype(dtype) - offset) / abs_max

def float_to_pcm(sig, dtype='int16'):
    sig = np.asarray(sig)
    if sig.dtype.kind != 'f':
        raise TypeError("'sig' must be a float array")
    dtype = np.dtype(dtype)
    if dtype.kind not in 'iu':
        raise TypeError("'dtype' must be an integer type")

    i = np.iinfo(dtype)
    abs_max = 2 ** (i.bits - 1)
    offset = i.min + abs_max
    return (sig * abs_max + offset).clip(i.min, i.max).astype(dtype)

def pcm24_to_32(data, channels=1, normalize=True):
    if len(data) % 3 != 0:
        raise ValueError('Size of data must be a multiple of 3 bytes')

    out = np.zeros(len(data) // 3, dtype='<i4')
    out.shape = -1, channels
    temp = out.view('uint8').reshape(-1, 4)
    if normalize:
        # write to last 3 columns, leave LSB at zero
        columns = slice(1, None)
    else:
        # write to first 3 columns, leave MSB at zero
        columns = slice(None, -1)
    temp[:, columns] = np.frombuffer(data, dtype='uint8').reshape(-1, 3)
    return out

class MicStream(object):
    def __init__(self):
        self.p = None
        self.pyaudio_stream = None
        self.byte_buffer = bytes()
        self.is_running = False
        self.stream_sample_rate = 44100
        self.output_sample_rate = 48000
        self.read_time = 0.02
        self.edge_time = 0.005

    def is_active(self):
        return self.pyaudio_stream.is_active()

    def start(self):
        self.is_running = True
        self.p = pyaudio.PyAudio()
        self.pyaudio_stream = self.p.open(
            format=pyaudio.paInt24,
            channels=2,
            rate=self.stream_sample_rate,
            input=True,
            output=False,
            stream_callback=self._callback,
            frames_per_buffer=1024,
        )

    def stop(self):
        if self.is_running:
            self.pyaudio_stream.close()
            self.p.terminate()
            self.is_running = False

    def read(self):
        channel_count = 2
        bytes_per_sample = 3
        edge_samples = int(self.edge_time * self.stream_sample_rate)
        read_samples = int(self.read_time * self.stream_sample_rate)
        resampled_read_samples = int(self.read_time * self.output_sample_rate)
        edge_bytes = edge_samples * channel_count * bytes_per_sample
        read_bytes = read_samples * channel_count * bytes_per_sample
        total_bytes = edge_bytes + read_bytes
        while True:
            if len(self.byte_buffer) >= read_bytes:
                raw_bytes = self.byte_buffer[0:read_bytes]
                data_pcm_32 = pcm24_to_32(raw_bytes, channels=channel_count)
                data_float = pcm_to_float(data_pcm_32)
                data_float_resampled = librosa.resample(
                    data_float.transpose(),
                    self.stream_sample_rate,
                    self.output_sample_rate,
                    res_type='kaiser_fast',
                    fix=False,
                )[:, 0:resampled_read_samples].transpose()
                data_pcm_16 = float_to_pcm(data_float_resampled)
                data_pcm_16_transposed = data_pcm_16.transpose()
                data_pcm_16_left = data_pcm_16_transposed[0]
                data_pcm_16_right = data_pcm_16_transposed[1]
                interleaved_pcm = interleave_arrays(data_pcm_16_left, data_pcm_16_right)
                self.byte_buffer = self.byte_buffer[read_bytes:]
                return interleaved_pcm.tobytes()

    def _callback(self, in_data, frame_count, time_info, flag):
        self.byte_buffer += in_data
        return None, pyaudio.paContinue